# parse_invoice_lambda.py
import json
import base64
import io
import re
import openai
import PyPDF2
import pytesseract
from pdf2image import convert_from_bytes
from PIL import Image

def lambda_handler(event, context):
    """
    1) PDFバイナリをBase64で受け取り
    2) use_ocr=Trueの場合はOCR + ChatGPT でJSON化
    3) JSONレスポンスを返す
    """
    openai_api_key = event.get("openai_api_key")
    if not openai_api_key:
        raise ValueError("OpenAI API key is required")
    openai.api_key = openai_api_key

    file_bytes_b64 = event.get("file_bytes", "")
    if not file_bytes_b64:
        raise ValueError("File bytes are required")
    
    file_bytes = base64.b64decode(file_bytes_b64)
    use_ocr = event.get("use_ocr", True)  # Default to True for auto-detection

    # PDFをテキスト化
    raw_text = extract_text_from_pdf(file_bytes, use_ocr)

    # ChatGPTでJSON化
    unified_text = unify_text_via_openai(raw_text)

    # JSONパース
    structured_data = extract_fields_from_text(unified_text)

    # 14項目にマッピング
    invoice_data = parse_invoice_data(structured_data)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "invoice_data": invoice_data
        })
    }

def extract_text_from_pdf(pdf_bytes, use_ocr=True):
    """
    PDFから文字を抽出する。
    画像PDFの場合、use_ocr=True で Tesseract OCRを呼び出す。
    日本語テキストの場合は常にOCRを試みる。
    """
    text_all = ""
    is_japanese = False

    # First try normal PDF text extraction
    try:
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted and extracted.strip():
                text_all += extracted + "\n"
                # Check if text contains Japanese characters
                if any(ord(c) > 0x3000 for c in extracted):
                    is_japanese = True
    except Exception as e:
        print(f"PDF text extraction failed: {e}")
        
    # Try OCR if:
    # 1. No text was extracted, or
    # 2. OCR is forced, or
    # 3. Japanese text was detected
    if not text_all.strip() or use_ocr or is_japanese:

        # OCRを実行 (pdf2image + pytesseract)
        images = convert_from_bytes(pdf_bytes)

        for img in images:
            output = io.BytesIO()
            # PDF2Image で得られた PIL Image を PNG化
            img.save(output, format="PNG")
            image_binary = output.getvalue()

            # 5MB超なら分割
            splitted_binaries = split_image_if_needed(image_binary)

            # 分割後バイナリを順次OCRして連結
            for sbin in splitted_binaries:
                try:
                    # First try Japanese + English OCR with horizontal text
                    text_page = pytesseract.image_to_string(
                        Image.open(io.BytesIO(sbin)), 
                        lang='jpn+eng',
                        config='--psm 6'  # Assume uniform block of text
                    )
                    
                    # If no text found or very little text, try vertical Japanese text
                    if len(text_page.strip()) < 10:
                        text_page_vert = pytesseract.image_to_string(
                            Image.open(io.BytesIO(sbin)), 
                            lang='jpn_vert+jpn',
                            config='--psm 5'  # Assume vertical block of text
                        )
                        if len(text_page_vert.strip()) > len(text_page.strip()):
                            text_page = text_page_vert
                            
                except Exception as e:
                    print(f"OCR error: {e}")
                    text_page = ""
                
                if text_page.strip():
                    text_all += text_page.strip() + "\n"

    return text_all

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

def split_image_if_needed(image_binary):
    """
    画像バイナリを読み込んで、5MB超の場合は縦半分に分割する。
    分割後も5MBを超える場合はエラーとする。
    ※サンプル実装なので必要に応じてカスタマイズ
    """
    if len(image_binary) <= MAX_IMAGE_SIZE:
        # 5MB以下なら分割不要
        return [image_binary]

    try:
        img = Image.open(io.BytesIO(image_binary))
        width, height = img.size
        half_height = height // 2

        split_binaries = []
        for i in range(2):
            top = i * half_height
            bottom = (i + 1) * half_height if i < 1 else height

            cropped_img = img.crop((0, top, width, bottom))
            output = io.BytesIO()
            # PNG形式で保存
            cropped_img.save(output, format="PNG")
            cropped_binary = output.getvalue()

            if len(cropped_binary) > MAX_IMAGE_SIZE:
                raise ValueError("Split image size still exceeds 5MB limit.")
            
            split_binaries.append(cropped_binary)
        
        return split_binaries

    except Exception as e:
        raise ValueError(f"Error during image splitting: {e}")

# --- OpenAI 表記ゆれ補正関数 ---
def unify_text_via_openai(raw_text):
    """
    大幅な表記ゆれがあるテキストを OpenAI の GPT-4 モデルで整形・標準化。
    """
    if not openai.api_key:
        raise ValueError("OpenAI APIキーが設定されていません。")

    print("raw_text=================================")
    print(raw_text)

    try:
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "あなたは優秀なアシスタントです。"
                },
                {
                    "role": "user",
                    "content": f"""与えられた請求書に記載されたテキストを構造的に解釈して、JSON形式に整理してください。
                    ・必須で取得が可能な項目：「発注番号」「金額」「物件名（建物名）」「部屋番号」「工事業者名」
                    ・その他項目は可能であれば取得
                    ・純粋なjson形式のみで回答してください
                    ・内容が重複している情報は不要です
                    ・全角スペース、半角スペースは各項目の値に含めないでください
                    ---回答フォーマット（例）:
                    [
                        {{
                            "発注番号": "12345",
                            "金額": "100000",
                            "物件名": "サンプル物件",
                            "部屋番号": "101",
                            "工事業者名": "サンプル工事会社"
                        }},
                        ...
                    ]
                    ---テキスト内容:
                    {raw_text}
                """
                }
            ],
            max_tokens=4000,
            temperature=0
        )

        cleaned_text = response.choices[0].message.content.strip()

        print("cleaned_text====================================")
        print(cleaned_text)
        return cleaned_text
    except Exception as e:
        print(f"OpenAI API error: {e}")
        return raw_text


# --- PDFテキストから各項目を抽出する関数 ---
def extract_fields_from_text(text):
    """
    テキストから発注番号、金額、物件名、部屋番号、工事業者名を抽出する
    """
    # JSON部分を抽出
    match = re.search(r'```json\n(\[.*?\])\n```', text, re.DOTALL)
    if match:
        json_data_str = match.group(1)  # Matchオブジェクトから文字列を取得
    else:
        json_data_str = text.strip()  # そのままテキストを取得

    try:
        invoice_data = json.loads(json_data_str)  # JSON文字列を辞書に変換
        structured_data = []

        for entry in invoice_data:
            structured_data.append({
                "発注番号": entry.get("発注番号", "不明"),
                "金額": entry.get("金額", "不明"),
                "物件名": entry.get("物件名", "不明"),
                "部屋番号": entry.get("部屋番号", "不明"),
                "工事業者名": entry.get("工事業者名", "不明")
            })

        return structured_data
    except json.JSONDecodeError:
        print("JSONの解析に失敗しました。")
        return []

def parse_invoice_data(text):
    # すでに pdf_data はリスト of dict なので、そのまま14項目を埋める処理だけ行う。
    structured_data = []
    for entry in text:  # pdf_data は extract_fields_from_text の戻り値(list)
        structured_data.append({
            "発注番号": entry.get("発注番号", "不明"),
            "金額": entry.get("金額", "不明"),
            "物件名": entry.get("物件名", "不明"),
            "部屋番号": entry.get("部屋番号", "不明"),
            "工事業者名": entry.get("工事業者名", "不明"),
            "業者ID": entry.get("業者ID", "不明"),
            "コード": entry.get("コード", "不明"),
            "受付内容": entry.get("受付内容", "不明"),
            "支払金額": entry.get("支払金額", "不明"),
            "修繕作成者": entry.get("修繕作成者", "不明"),
            "完工日": entry.get("完工日", "不明"),
            "修繕業者ID": entry.get("修繕業者ID", "不明"),
            "支払サイト": entry.get("支払サイト", "不明"),
            "支払日": entry.get("支払日", "不明"),
            "立替金": entry.get("立替金", "不明"),
            "請求日": entry.get("請求日", "不明")
        })
    return structured_data
