from paddleocr import PaddleOCR
import cv2
import json

def create_json(image_path):
    # Initialize the PaddleOCR model
    ocr = PaddleOCR(use_angle_cls=True, lang='en')  # Set lang to your desired language

    # Perform OCR
    results = ocr.ocr(image_path, cls=True)

    # Prepare JSON output
    output = []

    for line in results:
        for word_info in line:
            box = word_info[0]  # Bounding box
            text = word_info[1][0]  # Extracted text
            confidence = word_info[1][1]  # Confidence score
            output.append({
                "bounding_box": box,
                "text": text,
                "confidence": confidence
            })

    # Convert to JSON format
    json_output = json.dumps(output, indent=4)

    # Print or save the output
    # print(json_output)

    return json_output

    # Optionally, save to a file
    # Save the extracted text and bounding boxes to a JSON file
    # with open(f'static/output_{image_path.split("/")[-1]}.json', 'w') as f:
    #     f.write(json_output)


