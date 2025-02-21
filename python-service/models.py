from pydantic import BaseModel
from typing import List, Optional

class OrderData(BaseModel):
    業者ID: str
    業者名: str
    建物名: str
    番号: str
    受付内容: str
    支払金額: str
    完工日: str
    支払日: str
    請求日: str

class InvoiceData(BaseModel):
    発注番号: str
    金額: str
    物件名: str
    部屋番号: str
    工事業者名: str

class MatchResponse(BaseModel):
    diff_rows: List[dict]

class ParseResponse(BaseModel):
    parsed_orders: List[OrderData]

class InvoiceResponse(BaseModel):
    invoice_data: List[InvoiceData]
