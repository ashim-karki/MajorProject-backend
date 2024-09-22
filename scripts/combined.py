import torch
from transformers import AutoModelForObjectDetection, TableTransformerForObjectDetection
from torchvision import transforms
from paddleocr import PaddleOCR
from tqdm.auto import tqdm
from PIL import Image
import numpy as np
import csv
import logging

def tatr_function(img_path):
    # Set logging level
    logging.getLogger().setLevel(logging.CRITICAL)

    # --- Script 1: cell coordinates ---
    def get_cell_coordinates_by_row(table_data):
        rows = [entry for entry in table_data if entry['label'] == 'table row']
        columns = [entry for entry in table_data if entry['label'] == 'table column']

        rows.sort(key=lambda x: x['bbox'][1])
        columns.sort(key=lambda x: x['bbox'][0])

        def find_cell_coordinates(row, column):
            cell_bbox = [column['bbox'][0], row['bbox'][1], column['bbox'][2], row['bbox'][3]]
            return cell_bbox

        cell_coordinates = []
        for row in rows:
            row_cells = []
            for column in columns:
                cell_bbox = find_cell_coordinates(row, column)
                row_cells.append({'column': column['bbox'], 'cell': cell_bbox})

            row_cells.sort(key=lambda x: x['column'][0])
            cell_coordinates.append({'row': row['bbox'], 'cells': row_cells, 'cell_count': len(row_cells)})

        cell_coordinates.sort(key=lambda x: x['row'][1])
        return cell_coordinates


    # --- Script 2: object detection and cropping ---
    def objects_to_crops(img, tokens, objects, class_thresholds, padding=10):
        table_crops = []
        for obj in objects:
            if obj['score'] < class_thresholds[obj['label']]:
                continue

            bbox = obj['bbox']
            bbox = [bbox[0]-padding, bbox[1]-padding, bbox[2]+padding, bbox[3]+padding]
            cropped_img = img.crop(bbox)
            table_tokens = [token for token in tokens if iob(token['bbox'], bbox) >= 0.5]

            for token in table_tokens:
                token['bbox'] = [token['bbox'][0]-bbox[0], token['bbox'][1]-bbox[1],
                                token['bbox'][2]-bbox[0], token['bbox'][3]-bbox[1]]

            if obj['label'] == 'table rotated':
                cropped_img = cropped_img.rotate(270, expand=True)
                for token in table_tokens:
                    bbox = token['bbox']
                    bbox = [cropped_img.size[0]-bbox[3]-1, bbox[0], cropped_img.size[0]-bbox[1]-1, bbox[2]]
                    token['bbox'] = bbox

            table_crops.append({'image': cropped_img, 'tokens': table_tokens})
        return table_crops


    # --- Script 3: loading the model and processing image ---
    model = AutoModelForObjectDetection.from_pretrained("microsoft/table-transformer-detection", revision="no_timm")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model.to(device)

    file_path = img_path  # Change to the correct file path
    image = Image.open(file_path).convert("RGB")
    width, height = image.size


    # --- Script 4: OCR and extracting structured data ---
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    structured_data = []

    def apply_ocr(cell_coordinate, crop):
        data = dict()
        max_num_columns = 0
        for idx, row in enumerate(tqdm(cell_coordinate)):
            row_text = []
            for cell in row["cells"]:
                cell_image = np.array(crop.crop(cell["cell"]))
                result = ocr.ocr(cell_image)
                if result == [None]:
                    row_text.append("")
                else:
                    text = " ".join([line[1][0] for line in result[0]])
                    row_text.append(text)
            if len(row_text) > max_num_columns:
                max_num_columns = len(row_text)
            data[idx] = row_text

        for row, row_data in data.copy().items():
            if len(row_data) != max_num_columns:
                row_data = row_data + ["" for _ in range(max_num_columns - len(row_data))]
            data[row] = row_data
        return data


    # --- Script 5: resize and post-process outputs ---
    class MaxResize(object):
        def __init__(self, max_size=800):
            self.max_size = max_size

        def __call__(self, image):
            width, height = image.size
            current_max_size = max(width, height)
            scale = self.max_size / current_max_size
            return image.resize((int(round(scale * width)), int(round(scale * height))))

    detection_transform = transforms.Compose([
        MaxResize(800),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    pixel_values = detection_transform(image).unsqueeze(0).to(device)
    with torch.no_grad():
        outputs = model(pixel_values)

    def box_cxcywh_to_xyxy(x):
        x_c, y_c, w, h = x.unbind(-1)
        b = [(x_c - 0.5 * w), (y_c - 0.5 * h), (x_c + 0.5 * w), (y_c + 0.5 * h)]
        return torch.stack(b, dim=1)

    def rescale_bboxes(out_bbox, size):
        img_w, img_h = size
        b = box_cxcywh_to_xyxy(out_bbox)
        return b * torch.tensor([img_w, img_h, img_w, img_h], dtype=torch.float32)

    def outputs_to_objects(outputs, img_size, id2label):
        m = outputs.logits.softmax(-1).max(-1)
        pred_labels = list(m.indices.detach().cpu().numpy())[0]
        pred_scores = list(m.values.detach().cpu().numpy())[0]
        pred_bboxes = outputs['pred_boxes'].detach().cpu()[0]
        pred_bboxes = [elem.tolist() for elem in rescale_bboxes(pred_bboxes, img_size)]

        objects = []
        for label, score, bbox in zip(pred_labels, pred_scores, pred_bboxes):
            class_label = id2label.get(int(label), "unknown")  # Use .get() to avoid KeyError
            if class_label != "no object":  # Filter out "no object"
                objects.append({'label': class_label, 'score': float(score),
                                'bbox': [float(elem) for elem in bbox]})
        return objects


    id2label = model.config.id2label
    id2label[len(model.config.id2label)] = "no object"
    objects = outputs_to_objects(outputs, image.size, id2label)


    # --- Script 6: structure recognition ---
    structure_model = TableTransformerForObjectDetection.from_pretrained("microsoft/table-structure-recognition-v1.1-all")
    structure_model.to(device)
    cropped_table = objects_to_crops(image, [], objects, {"table": 0.5, "table rotated": 0.5, "no object": 10})
    outputs, cells = [], []

    structure_transform = transforms.Compose([
        MaxResize(1000),
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    ])

    for crop in cropped_table:
        pixel_values = structure_transform(crop['image']).unsqueeze(0).to(device)
        with torch.no_grad():
            output = structure_model(pixel_values)
            outputs.append(output)

    for i in range(len(cropped_table)):
        cell = outputs_to_objects(outputs[i], cropped_table[i]['image'].size, structure_model.config.id2label)
        cells.extend([cell])

    cell_coordinates = [get_cell_coordinates_by_row(cell) for cell in cells]
    structured_data = []

    for i in range(len(cell_coordinates)):
        data = apply_ocr(cell_coordinates[i], cropped_table[i]['image'])
        structured_data.extend([data])

    final_output = []
    for data in structured_data:
        for row, row_text in data.items():
            final_output.extend([row_text])

    with open('output.csv', 'w') as result_file:  # Change to the correct file path
        wr = csv.writer(result_file, dialect='excel')
        for row_text in final_output:
            wr.writerow(row_text)
