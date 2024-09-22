# api/extract_text_api.py

from fastapi import APIRouter, Request
import json
from scripts import paddle_bbox

# Define the router with a prefix for '/api'
router = APIRouter()

@router.post("/extracttext")
async def extract_text(request: Request):
    label = ""
    image_url = ""

    form = await request.form()
    upload_file = form["upload_file_1"]
    contents = await upload_file.read()

    # Save the uploaded image
    image_filename = f"static/uploaded_files/{upload_file.filename}"
    with open(image_filename, "wb") as f:
        f.write(contents)

    image_url = f"static/uploaded_files/{upload_file.filename}"

    # Assuming paddle_bbox.create_json returns the bounding box data as JSON
    output_string = paddle_bbox.create_json(image_url)
    output_json = json.loads(output_string)

    bounding_boxes = []
    for item in output_json:
        if isinstance(item, dict):
            box = item["bounding_box"]
            text = item["text"]
            # Convert box coordinates into a usable format for the frontend
            x, y, width, height = box[0][0], box[0][1], box[2][0] - box[0][0], box[2][1] - box[0][1]
            bounding_boxes.append({
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "text": text
            })

    return {
        "image_url": image_url,
        "annotated_image_url": image_url,  # Just returning the same for this example
        "bounding_boxes": bounding_boxes
    }
