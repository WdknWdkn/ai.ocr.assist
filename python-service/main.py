from fastapi import FastAPI, UploadFile
from PIL import Image
import pytesseract

app = FastAPI()

@app.get("/")
def read_root():
    return {"status": "Python OCR Service is running"}

@app.post("/ocr")
async def perform_ocr(file: UploadFile):
    image = Image.open(file.file)
    text = pytesseract.image_to_string(image, lang='jpn+eng')
    return {"text": text}
