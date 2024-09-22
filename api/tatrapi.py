# api/tatrapi.py

from fastapi import APIRouter, Request
import json
from scripts import table_transformer

# Define the router with a prefix for '/api'
router = APIRouter()

@router.post("/tatr")
async def tatr(request: Request):
    label = ""
    image_url = ""

    form = await request.form()
    upload_file = form["upload_file"]
    contents = await upload_file.read()

    # Save the uploaded image
    image_filename = f"static/uploaded_files/{upload_file.filename}"
    with open(image_filename, "wb") as f:
        f.write(contents)

    image_url = f"static/uploaded_files/{upload_file.filename}"