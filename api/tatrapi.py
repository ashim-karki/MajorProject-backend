from fastapi import APIRouter, UploadFile, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from PIL import Image
import csv
import traceback
from io import StringIO, BytesIO
from scripts.combined import tatr_function
import logging
from starlette.concurrency import run_in_threadpool

router = APIRouter()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@router.post("/tatr")
async def process_image(file: UploadFile, request: Request):
    if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a PNG or JPEG image.")

    try:
        # Read file content
        content = await file.read()
        
        # Check file size (10 MB limit)
        if len(content) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="File too large. Maximum size is 10 MB.")

        # Create a BytesIO object instead of saving to disk
        image_stream = BytesIO(content)

        # Verify it's a valid image
        try:
            with Image.open(image_stream) as img:
                img.verify()
            image_stream.seek(0)
        except Exception as e:
            logger.error(f"Invalid image file: {str(e)}")
            raise HTTPException(status_code=400, detail="Invalid image file.")

        # Call tatr_function and get CSV data
        logger.info(f"Processing image: {file.filename}")
        output_csv_data = await run_in_threadpool(tatr_function, image_stream)

        # Check if output_csv_data is None or empty
        # if not output_csv_data:
        #     logger.error("tatr_function returned None or empty data")
        #     raise HTTPException(status_code=500, detail="Image processing failed to produce any data.")

        logger.info(f"Successfully processed image: {file.filename}")

        # Convert CSV to stream for streaming response
        csv_stream = StringIO()
        csv_writer = csv.writer(csv_stream)
        csv_writer.writerows(output_csv_data)

        csv_stream.seek(0)
        
        # Return the CSV as a streaming response
        return StreamingResponse(
            csv_stream, 
            media_type="text/csv", 
            headers={"Content-Disposition": f"attachment; filename=output_{file.filename}.csv"}
        )
    
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error processing image {file.filename}: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Hide detailed error information from users for security
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again later.")
