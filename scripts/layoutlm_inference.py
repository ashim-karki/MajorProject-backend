from transformers import LayoutLMForTokenClassification, LayoutLMv2Processor
from PIL import Image, ImageDraw, ImageFont
import torch

# Load model and processor from Hugging Face hub
def load_model_and_processor(model_path, processor_path):
    model = LayoutLMForTokenClassification.from_pretrained(model_path)
    processor = LayoutLMv2Processor.from_pretrained(processor_path)
    return model, processor

# Helper function to unnormalize bboxes
def unnormalize_box(bbox, width, height):
    return [
        width * (bbox[0] / 1000),
        height * (bbox[1] / 1000),
        width * (bbox[2] / 1000),
        height * (bbox[3] / 1000),
    ]

# Drawing function to visualize boxes and labels
def draw_boxes(image, boxes, predictions, label2color):
    width, height = image.size
    normalized_boxes = [unnormalize_box(box, width, height) for box in boxes]

    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()

    for prediction, box in zip(predictions, normalized_boxes):
        if prediction == "O":
            continue
        draw.rectangle(box, outline=label2color.get(prediction, "black"))
        draw.text((box[0] + 10, box[1] - 10), text=prediction, fill=label2color.get(prediction, "black"), font=font)
    return image

# Running inference
def run_inference(image_path, model, processor, label2color, output_image=True):
    image = Image.open(image_path).convert("RGB")
    encoding = processor(image, return_tensors="pt")
    del encoding["image"]

    input_ids = encoding['input_ids']
    bbox = encoding['bbox']

    outputs = model(**encoding)
    predictions = outputs.logits.argmax(-1).squeeze().tolist()
    labels = [model.config.id2label[pred] for pred in predictions]

    if output_image:
        return draw_boxes(image, bbox[0], labels, label2color), labels, input_ids, bbox
    return labels, input_ids, bbox

# Merging tokens that are split
def merge_tokens(tokens, labels, bboxes):
    merged_tokens, merged_labels, merged_bboxes = [], [], []
    for i, token in enumerate(tokens):
        if token.startswith("##"):
            merged_tokens[-1] += token[2:]
            merged_bboxes[-1] = [merged_bboxes[-1][0], merged_bboxes[-1][1], bboxes[i][2], merged_bboxes[-1][3]]
        else:
            merged_tokens.append(token)
            merged_labels.append(labels[i])
            merged_bboxes.append(bboxes[i])
    return merged_tokens, merged_labels, merged_bboxes

# Grouping tokens by lines based on y-coordinates
def group_by_lines(tokens, labels, bboxes):
    lines = []
    current_line = []
    current_y = bboxes[0][1]

    for i, (token, label, bbox) in enumerate(zip(tokens, labels, bboxes)):
        if bbox[1] > current_y + 10:  # Allowing a threshold to detect new lines
            lines.append(current_line)
            current_line = []
            current_y = bbox[1]
        current_line.append((token, label, bbox))
    
    if current_line:
        lines.append(current_line)
    
    return lines

# Extracting question-answer pairs
def extract_qa_pairs(lines):
    result = []
    current_question = []
    current_answer = []

    for line in lines:
        for token, label, _ in line:
            if label.startswith("B-QUESTION"):
                if current_question and current_answer:
                    result.append({" ".join(current_question): " ".join(current_answer)})
                    current_question = []
                    current_answer = []
                current_question.append(token)
            elif label.startswith("I-QUESTION"):
                current_question.append(token)
            elif label.startswith("B-ANSWER"):
                current_answer.append(token)
            elif label.startswith("I-ANSWER"):
                current_answer.append(token)

    if current_question and current_answer:
        result.append({" ".join(current_question): " ".join(current_answer)})

    return result

# Full pipeline to process the image and extract Q&A pairs
def process_image(image_path, model, processor, label2color):
    image, labels, input_ids, bboxes = run_inference(image_path, model, processor, label2color)

    tokens = processor.tokenizer.convert_ids_to_tokens(input_ids[0])
    merged_tokens, merged_labels, merged_bboxes = merge_tokens(tokens, labels, bboxes[0])
    lines = group_by_lines(merged_tokens, merged_labels, merged_bboxes)
    qa_pairs = extract_qa_pairs(lines)

    return image, qa_pairs