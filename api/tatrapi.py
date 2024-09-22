from fastapi import APIRouter, File, UploadFile, HTTPException
from fastapi.responses import FileResponse
from PIL import Image
import os
from scripts.combined import tatr_function

router = APIRouter()

@router.post("/tatr")
async def process_image(file: UploadFile = File(...)):
    # Check for valid image file types
    # if not file.filename.endswith(('.png', '.jpg', '.jpeg')):
    #     raise HTTPException(status_code=400, detail="Invalid file type. Please upload a valid image (PNG, JPG, or JPEG).")

    try:
        # Save the uploaded file temporarily
        temp_file_path = f"temp_{file.filename}"
        with open(temp_file_path, "wb") as temp_file:
            content = await file.read()
            temp_file.write(content)

        # Call the TATR processing function (assuming it returns the path to the CSV file)
        output_csv_path = tatr_function(temp_file_path)

        # Remove the temp image file after processing
        # os.remove(temp_file_path)

        # Return the generated CSV file as a response
        return FileResponse(output_csv_path, filename="output.csv", media_type='text/csv')

    except Exception as e:
        # Handle any errors and return a 500 Internal Server Error with the message
        raise HTTPException(status_code=500, detail=f"Image processing failed: {str(e)}")
