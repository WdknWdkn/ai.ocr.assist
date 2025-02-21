from fastapi import FastAPI, UploadFile, File, HTTPException
from typing import List
import io
import base64
from . import models, utils
from .match_lambda import match_csv_and_pdf
from .parse_invoice_lambda import extract_text_from_pdf, unify_text_via_openai, extract_fields_from_text
from .parse_order_lambda import parse_csv, parse_excel

app = FastAPI(title="OCR Assistant API")

@app.post("/api/v1/orders/parse", response_model=models.ParseResponse)
async def parse_orders(file: UploadFile = File(...)):
    utils.validate_file_size(file.size)
    content = await file.read()
    
    if file.filename.lower().endswith(('.xlsx', '.xls')):
        result = parse_excel(content)
    else:
        result = parse_csv(content)
    
    return {"parsed_orders": result}

@app.post("/api/v1/invoices/parse", response_model=models.InvoiceResponse)
async def parse_invoice(
    file: UploadFile = File(...),
    use_ocr: bool = True
):
    utils.validate_file_size(file.size)
    content = await file.read()
    
    text = extract_text_from_pdf(content, use_ocr)
    unified_text = unify_text_via_openai(text)
    structured_data = extract_fields_from_text(unified_text)
    
    return {"invoice_data": structured_data}

@app.post("/api/v1/match", response_model=models.MatchResponse)
async def match_documents(
    orders_file: UploadFile = File(...),
    invoices_file: UploadFile = File(...)
):
    utils.validate_file_size(orders_file.size)
    utils.validate_file_size(invoices_file.size)
    
    orders_content = await orders_file.read()
    invoices_content = await invoices_file.read()
    
    if orders_file.filename.lower().endswith(('.xlsx', '.xls')):
        orders = parse_excel(orders_content)
    else:
        orders = parse_csv(orders_content)
    
    invoice_text = extract_text_from_pdf(invoices_content, True)
    unified_text = unify_text_via_openai(invoice_text)
    invoices = extract_fields_from_text(unified_text)
    
    diff_rows = match_csv_and_pdf(orders, invoices)
    return {"diff_rows": diff_rows}
