from pydantic import BaseModel
from typing import Optional, Dict, Any

class ParseResponse(BaseModel):
    message: str
    data: Dict[str, Any]

class InvoiceResponse(BaseModel):
    message: str
    text: str

class MatchResponse(BaseModel):
    message: str
    orders: Dict[str, Any]
    invoice_text: str
