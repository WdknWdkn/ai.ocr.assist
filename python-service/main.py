import os
import sys
import traceback
import base64
import json
import io
import pandas as pd
import PyPDF2
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Optional
import uvicorn

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

import parse_invoice_lambda
from parse_order_lambda import parse_csv, parse_excel
import re


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
            detail="ファイルの形式が正しくありません。CSVまたはExcelファイルを選択してください。"
        )
    
    try:
        content = await file.read()
        content_length = len(content)
        print(f"Processing file: {file.filename} ({content_length} bytes)", file=sys.stderr)
        
        if content_length > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail="ファイルサイズは1MB以下にしてください。"
            )
        
        if file.filename.endswith('.xlsx'):
            result = parse_excel(content)
        else:
            result = parse_csv(content)
            
        if not isinstance(result, dict):
            raise ValueError("不正な出力形式です。")
            
        orders = result["orders"]
        total_rows = result["total_rows"]
        skipped_rows = result["skipped_rows"]
        valid_rows = result["valid_rows"]
        
        print(f"Processed {total_rows} rows: {valid_rows} valid, {skipped_rows} skipped", file=sys.stderr)
            
        return {
            "message": f"{valid_rows}件の有効なデータを処理しました。{skipped_rows}件のデータをスキップしました。",
            "data": orders
        }
    except ValueError as e:
        print(f"Validation error: {str(e)}", file=sys.stderr)
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Error in parse_orders: {str(e)}\n{traceback.format_exc()}", file=sys.stderr)
        raise HTTPException(
            status_code=500,
            detail="ファイルの解析中にエラーが発生しました。"
        )

@app.post("/api/v1/invoices/parse")
async def parse_invoice(file: UploadFile, use_ocr: Optional[bool] = None):
    """
    PDFまたは画像ファイルを受け取り、請求書データを抽出する
    """
    print("========== 処理開始: FastAPI 請求書解析エンドポイント ==========")
    print(f"ファイル名: {file.filename}, OCR使用フラグ: {use_ocr}")
    
    # ファイル形式の検証
    print("ファイル形式の検証")
    if not file.filename.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png')):
        print(f"エラー: 不正なファイル形式: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail="ファイルの形式が正しくありません。PDF、JPG、またはPNG形式のファイルを選択してください。"
        )

    try:
        # ファイルの読み込み
        print("ファイルの読み込み開始")
        content = await file.read()
        content_size = len(content)
        print(f"ファイルサイズ: {content_size} バイト")
        
        # ファイルサイズの検証
        print("ファイルサイズの検証")
        if content_size > MAX_FILE_SIZE:
            print(f"エラー: ファイルサイズ超過: {content_size} バイト (上限: {MAX_FILE_SIZE} バイト)")
            raise HTTPException(
                status_code=413,
                detail="ファイルサイズは1MB以下にしてください。"
            )

        # Base64エンコード
        print("ファイルデータのBase64エンコード")
        file_bytes_b64 = base64.b64encode(content).decode()
        print(f"Base64エンコード後のサイズ: {len(file_bytes_b64)} 文字")

        # OpenAI APIキーの取得
        print("OpenAI APIキーの取得")
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            print("警告: OpenAI APIキーが見つかりません。モック実装を使用します。")
            openai_api_key = "sk-mock-key-for-testing"
            print("モックAPIキーを設定しました")
            # Continue with mock key - the mock_openai.py will be used automatically
            # when the real OpenAI module is not available

        try:
            # Lambda関数の呼び出し
            print("========== Lambda関数の呼び出し ==========")
            use_ocr_value = True if use_ocr is not None else False
            print(f"Lambda関数パラメータ: use_ocr={use_ocr_value}, APIキー長={len(openai_api_key)}")
            
            # Process with lambda handler
            result = parse_invoice_lambda.lambda_handler({
                "file_bytes": file_bytes_b64,
                "openai_api_key": openai_api_key,
                "use_ocr": use_ocr_value  # Fixed type handling
            }, None)

            # 結果の検証
            print("Lambda関数の実行結果の検証")
            if result is None:
                print("エラー: Lambda関数の結果がNoneです")
                raise ValueError("請求書の解析に失敗しました。")
            
            print(f"Lambda関数のステータスコード: {result.get('statusCode')}")
            
            # レスポンスのパース
            print("レスポンスJSONのパース")
            parsed_result = json.loads(result["body"])
            
            # レスポンスの作成
            print("クライアントへのレスポンス作成")
            response = {
                "message": parsed_result.get("message", "請求書の解析が完了しました。"),
                "invoice_data": parsed_result.get("invoice_data", []),
                "text": parsed_result.get("text", "")
            }
            
            print(f"抽出されたデータ項目数: {len(response['invoice_data'])}")
            print("========== 処理完了: 正常終了 ==========")
            return response

        except ValueError as e:
            print(f"エラー: 値エラー: {str(e)}")
            print("========== 処理完了: バリデーションエラー ==========")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            print(f"エラー: 予期しないエラー: {str(e)}")
            print(f"詳細なスタックトレース:\n{traceback.format_exc()}", file=sys.stderr)
            print("========== 処理完了: 内部エラー ==========")
            raise HTTPException(
                status_code=500,
                detail="ファイルの解析中にエラーが発生しました。"
            )
    except HTTPException:
        # HTTPExceptionはそのまま再スロー
        raise
    except Exception as e:
        print(f"エラー: 予期しないエラー（ファイル処理）: {str(e)}")
        print(f"詳細なスタックトレース:\n{traceback.format_exc()}", file=sys.stderr)
        print("========== 処理完了: 内部エラー（ファイル処理） ==========")
        raise HTTPException(
            status_code=500,
            detail="ファイルの解析中にエラーが発生しました。"
        )

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
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=120,  # Increased from default to 120
        workers=2,
        limit_concurrency=4,
        timeout_graceful_shutdown=20  # Increased from default to 20
    )
