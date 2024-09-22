from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from starlette.requests import Request

# Import the router from the extract_text_api module
from api.extracttext import router as extract_text_router

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# Mount a directory to serve static files (uploaded images)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Ensure the 'static' directory exists to store uploaded images
Path("static").mkdir(exist_ok=True)

@app.get("/")
def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

# Include the extract_text API router with the '/api' prefix
app.include_router(extract_text_router, prefix="/api", tags=["extracttext"])


# USING OPENCV2

# def read_img(img):
#     text = pytesseract.image_to_string(img)
#     return text


# @app.post("/extract_text")
# async def extract_text(request: Request):
#     label = ""
#     image_url = ""

#     if request.method == "GET":
#         return RedirectResponse(url="/")
    
#     if request.method == "POST":
#         form = await request.form()
#         # Get the uploaded file
#         upload_file = form["upload_file"]
#         contents = await upload_file.read()

#         # Convert the uploaded image to an OpenCV format
#         image_stream = io.BytesIO(contents)
#         file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)
#         frame = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

#         # Save the uploaded image to the 'static' directory
#         image_filename = f"static/{upload_file.filename}"
#         with open(image_filename, "wb") as f:
#             f.write(contents)
        
#         # Set the URL for the saved image
#         image_url = f"static/{upload_file.filename}"

#         # Read text from the image using Tesseract
#         # label = read_img(frame)
#         output_string = paddle_bbox.create_json(image_url)
#         output_json = json.loads(output_string)
        
#         image = cv2.imread(image_url)

#         # output_data = json.loads(f'static/output_{upload_file.filename}.json')

#        # Draw bounding boxes and labels on the image
#         for item in output_json:
#             if isinstance(item, dict):
#                 box = np.array(item["bounding_box"], dtype=np.int32)
#                 text = item["text"]

#                 # Draw the bounding box
#                 cv2.polylines(image, [box], isClosed=True, color=(0, 0, 0), thickness=2)
#                 # Draw the text label
#                 cv2.putText(image, text, (int(box[0][0]), int(box[0][1] - 10)),
#                             cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 1)
#             else:
#                 return {"error": "Expected item to be a dictionary."}
#         output_path = "static/test.jpg"
#         cv2.imwrite(output_path, image)

    # Return the label and image URL to be displayed in the template
    # return templates.TemplateResponse("index.html", {"request": request, "label": label, "image_url": image_url, "annotated_image_url": output_path})
