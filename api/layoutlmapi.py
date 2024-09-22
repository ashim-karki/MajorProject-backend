from fastapi import APIRouter, UploadFile, File
from scripts.layoutlm_inference import load_model_and_processor, process_image
from PIL import Image
import os

router = APIRouter()

# Load model and processor once
model_path = "paudelanil/layoutlm"
processor_path = "microsoft/layoutlmv2-base-uncased"
model, processor = load_model_and_processor(model_path, processor_path)

# Define label to color mapping for drawing bounding boxes
label2color = {
    "B-HEADER": "blue",
    "B-QUESTION": "red",
    "B-ANSWER": "green",
    "I-HEADER": "blue",
    "I-QUESTION": "red",
    "I-ANSWER": "green",
}

# Ensure static output folder exists
OUTPUT_FOLDER = "static/uploaded_files"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

@router.post("/layout")
async def extract_qa_from_image(file: UploadFile = File(...), return_image: bool = False):
    # Read file contents as bytes
    file_bytes = await file.read()

    # Save the uploaded image
    image_path = os.path.join(OUTPUT_FOLDER, file.filename)
    with open(image_path, "wb") as buffer:
        buffer.write(file_bytes)

    # Resize the uploaded image
    uploaded_image = Image.open(image_path).resize((600, 800))  # Resize to 800x600
    uploaded_image.save(image_path)

    # Run the LayoutLM inference
    image_with_boxes, qa_pairs = process_image(image_path, model, processor, label2color)

    # Resize processed image before saving
    output_image_path = os.path.join(OUTPUT_FOLDER, f"processedlayout_{file.filename}")
    image_with_boxes = image_with_boxes.resize((600, 800))  # Resize to 800x600
    image_with_boxes.save(output_image_path)
    
    return {
        "qa_pairs": qa_pairs,
        "image_path": image_path,
        "output_image_path": output_image_path
    }
