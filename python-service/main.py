import os
import sys
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from typing import Optional
import json
import pandas as pd
import PyPDF2
from pdf2image import convert_from_bytes
import pytesseract
import io

# Import mock OpenAI for testing
if not os.getenv("OPENAI_API_KEY"):
    from mock_openai import Client as OpenAIClient
else:
    from openai import Client as OpenAIClient

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1MB

def validate_file_size(file_size: int):
    if file_size > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 1MB)")

from parse_order_lambda import parse_csv, parse_excel


async def extract_text_from_pdf(file: UploadFile, use_ocr: bool = False) -> str:
    content = await file.read()
    validate_file_size(len(content))
    
    if use_ocr:
        images = convert_from_bytes(content)
        text = ""
        for image in images:
            text += pytesseract.image_to_string(image, lang='jpn+eng') + "\n"
        return text
    else:
        pdf = PyPDF2.PdfReader(io.BytesIO(content))
        text = ""
        for page in pdf.pages:
            text += page.extract_text() + "\n"
        return text

@app.post("/api/v1/orders/parse")
async def parse_orders(file: UploadFile):
    if not file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(
            status_code=400,
            detail="ファイルの形式が正しくありません。"
        )
    
    try:
        content = await file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="ファイルサイズは1MB以下にしてください。"
            )
        
        if file.filename.endswith('.xlsx'):
            orders = parse_excel(content)
        else:
            orders = parse_csv(content)
            
        if not isinstance(orders, list):
            raise ValueError("不正な出力形式です。")
            
        return {"data": orders}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in parse_orders: {str(e)}", file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail="ファイルの解析中にエラーが発生しました。"
        )

@app.post("/api/v1/invoices/parse")
async def parse_invoice(file: UploadFile, use_ocr: Optional[bool] = False):
    if not file.filename.endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file format. Must be PDF")
    
    text = await extract_text_from_pdf(file, use_ocr)
    return {"message": "Invoice parsed successfully", "text": text}

@app.post("/api/v1/match")
async def match_documents(orders_file: UploadFile, invoices_file: UploadFile):
    if not orders_file.filename.endswith(('.csv', '.xlsx')):
        raise HTTPException(
            status_code=400,
            detail="ファイルの形式が正しくありません。"
        )
    if not invoices_file.filename.endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="PDFファイルを選択してください。"
        )
    
    try:
        content = await orders_file.read()
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="ファイルサイズは1MB以下にしてください。"
            )
        
        if orders_file.filename.endswith('.xlsx'):
            orders_data = parse_excel(content)
        else:
            orders_data = parse_csv(content)
            
        invoice_text = await extract_text_from_pdf(invoices_file, use_ocr=True)
        
        return {
            "data": {
                "orders": orders_data,
                "invoice_text": invoice_text
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail="ファイルの解析中にエラーが発生しました。"
        )

@app.get("/api/v1/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
