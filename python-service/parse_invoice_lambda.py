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

# Import logger
from logger import setup_logger
logger = setup_logger(__name__)

def lambda_handler(event, context):
    """
    1) PDFバイナリをBase64で受け取り
    2) use_ocr=Trueの場合はOCR + ChatGPT でJSON化
    3) JSONレスポンスを返す
    """
    logger.info("========== 処理開始: lambda_handler ==========")
    logger.info(f"イベントパラメータ: {event.keys()}")
    
    # OpenAI APIキーの取得
    logger.debug("OpenAI APIキーの取得")
    openai_api_key = event.get("openai_api_key")
    if not openai_api_key:
        logger.error("エラー: OpenAI APIキーが設定されていません")
        raise ValueError("OpenAI API key is required")
    logger.debug("OpenAI APIキーの設定完了")
    openai.api_key = openai_api_key

    # ファイルデータの取得
    logger.debug("ファイルデータの取得")
    file_bytes_b64 = event.get("file_bytes", "")
    if not file_bytes_b64:
        logger.error("エラー: ファイルデータが空です")
        raise ValueError("File bytes are required")
    
    # Base64デコード
    logger.debug("Base64デコードの実行")
    file_bytes = base64.b64decode(file_bytes_b64)
    logger.debug(f"デコード後のファイルサイズ: {len(file_bytes)} バイト")
    
    # OCRフラグの取得
    use_ocr = event.get("use_ocr", True)  # Default to True for auto-detection
    logger.debug(f"OCR使用フラグ: {use_ocr}")

    # ステップ1: PDFをテキスト化
    logger.info("========== ステップ1: PDFテキスト抽出 ==========")
    raw_text = extract_text_from_pdf(file_bytes, use_ocr)
    if not raw_text or not raw_text.strip():
        logger.error("エラー: PDFからテキストを抽出できませんでした")
        raise ValueError("テキストを抽出できませんでした。")
    logger.debug(f"抽出されたテキスト長: {len(raw_text)} 文字")
    logger.debug(f"テキストサンプル: {raw_text[:100]}...")

    # ステップ2: ChatGPTでJSON化
    logger.info("========== ステップ2: OpenAIによるテキスト処理 ==========")
    unified_text = unify_text_via_openai(raw_text)
    if not unified_text or not unified_text.strip():
        logger.error("エラー: OpenAIによるテキスト処理に失敗しました")
        raise ValueError("テキストを抽出できませんでした。")
    logger.debug(f"OpenAI処理後のテキスト長: {len(unified_text)} 文字")
    logger.debug(f"処理後テキストサンプル: {unified_text[:100]}...")

    # ステップ3: JSONパース
    logger.info("========== ステップ3: JSONパース ==========")
    structured_data = extract_fields_from_text(unified_text)
    if not structured_data:
        logger.error("エラー: JSONパースに失敗しました")
        raise ValueError("請求書からデータを抽出できませんでした。")
    logger.debug(f"抽出されたデータ項目数: {len(structured_data)}")
    logger.debug(f"抽出データサンプル: {structured_data[0] if structured_data else 'なし'}")

    # ステップ4: 14項目にマッピング
    logger.info("========== ステップ4: データマッピング ==========")
    invoice_data = parse_invoice_data(structured_data)
    if not invoice_data:
        logger.error("エラー: データマッピングに失敗しました")
        raise ValueError("請求書からデータを抽出できませんでした。")
    logger.debug(f"マッピング後のデータ項目数: {len(invoice_data)}")
    
    # テストデータのフォールバック
    if not invoice_data:
        logger.warning("警告: 抽出に失敗したためテストデータを使用します")
        invoice_data = [{
            "発注番号": "TEST-001",
            "金額": "50000",
            "物件名": "テスト物件",
            "部屋番号": "101",
            "工事業者名": "テスト工事会社",
            "請求書番号": "TEST-001",
            "発行日": "2025-01-01",
            "請求金額": "50000",
            "取引先名": "テスト株式会社",
            "支払期限": "2025-01-31",
            "備考": "テストデータ"
        }]
        logger.debug("テストデータの設定完了")

    # レスポンスの作成
    logger.info("========== 処理完了: レスポンス作成 ==========")
    response = {
        "statusCode": 200,
        "body": json.dumps({
            "message": "請求書の解析が完了しました。",
            "invoice_data": invoice_data,
            "text": raw_text or "請求書のテキストデータです"
        })
    }
    logger.debug(f"レスポンスステータス: {response['statusCode']}")
    logger.debug(f"請求書データ項目数: {len(invoice_data)}")
    logger.info("処理完了")
    return response

def extract_text_from_pdf(pdf_bytes, use_ocr=True):
    """
    PDFから文字を抽出する。
    画像PDFの場合、use_ocr=True で Tesseract OCRを呼び出す。
    日本語テキストの場合は常にOCRを試みる。
    """
    logger.debug(f"Starting PDF processing: {len(pdf_bytes)} bytes")
    text_all = ""
    is_japanese = False

    # First try normal PDF text extraction
    try:
        logger.debug("Attempting standard PDF text extraction...")
        reader = PyPDF2.PdfReader(io.BytesIO(pdf_bytes))
        total_pages = len(reader.pages)
        logger.debug(f"Processing {total_pages} pages")
        
        for i, page in enumerate(reader.pages, 1):
            logger.debug(f"Processing page {i}/{total_pages} with standard extraction")
            extracted = page.extract_text()
            if extracted and extracted.strip():
                text_all += extracted + "\n"
                # Check if text contains Japanese characters
                if any(ord(c) > 0x3000 for c in extracted):
                    is_japanese = True
                    logger.debug("Japanese text detected")
    except Exception as e:
        logger.error(f"PDF text extraction failed: {e}")
        
    # Try OCR if:
    # 1. No text was extracted, or
    # 2. OCR is forced, or
    # 3. Japanese text was detected
    if not text_all.strip() or use_ocr or is_japanese:
        logger.debug(f"Starting OCR processing (no text: {not text_all.strip()}, forced: {use_ocr}, japanese: {is_japanese})")

        # OCRを実行 (pdf2image + pytesseract)
        logger.debug("Converting PDF to images...")
        images = convert_from_bytes(pdf_bytes)
        logger.debug(f"Converted PDF to {len(images)} images")

        for i, img in enumerate(images, 1):
            logger.debug(f"Processing image {i}/{len(images)}")
            output = io.BytesIO()
            # PDF2Image で得られた PIL Image を PNG化
            img.save(output, format="PNG")
            image_binary = output.getvalue()
            logger.debug(f"Image {i} size: {len(image_binary)} bytes")

            # 5MB超なら分割
            logger.debug(f"Checking if image {i} needs splitting...")
            splitted_binaries = split_image_if_needed(image_binary)

            # 分割後バイナリを順次OCRして連結
            for sbin in splitted_binaries:
                try:
                    # Load and optimize image before OCR
                    img = Image.open(io.BytesIO(sbin))
                    img = optimize_image(img)
                    logger.debug(f"Image optimized to size: {img.size}")
                    
                    # First try Japanese + English OCR with horizontal text
                    text_page = pytesseract.image_to_string(
                        img,
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
                    logger.error(f"OCR error: {e}")
                    text_page = ""
                
                if text_page.strip():
                    text_all += text_page.strip() + "\n"

    return text_all

MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5MB

def optimize_image(img):
    """
    画像サイズを最適化する。
    2000px以上の画像はアスペクト比を保持しながらリサイズする。
    """
    width, height = img.size
    logger.debug(f"Original image size: {width}x{height}")
    if width > 2000 or height > 2000:
        ratio = min(2000/width, 2000/height)
        new_size = (int(width * ratio), int(height * ratio))
        logger.debug(f"Resizing image to: {new_size[0]}x{new_size[1]}")
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    return img

def split_image_if_needed(image_binary):
    """
    画像バイナリを読み込んで、5MB超の場合は縦半分に分割する。
    分割後も5MBを超える場合はエラーとする。
    ※サンプル実装なので必要に応じてカスタマイズ
    """
    logger.debug(f"Checking image size: {len(image_binary)} bytes")
    if len(image_binary) <= MAX_IMAGE_SIZE:
        # 5MB以下なら分割不要
        logger.debug("Image size is under limit, no splitting needed")
        return [image_binary]

    try:
        logger.info("Image exceeds size limit, splitting required")
        img = Image.open(io.BytesIO(image_binary))
        width, height = img.size
        half_height = height // 2
        logger.debug(f"Original image dimensions: {width}x{height}, splitting at height: {half_height}")

        split_binaries = []
        for i in range(2):
            top = i * half_height
            bottom = (i + 1) * half_height if i < 1 else height
            logger.debug(f"Cropping part {i+1}: from y={top} to y={bottom}")

            cropped_img = img.crop((0, top, width, bottom))
            output = io.BytesIO()
            # PNG形式で保存
            cropped_img.save(output, format="PNG")
            cropped_binary = output.getvalue()
            logger.debug(f"Split part {i+1} size: {len(cropped_binary)} bytes")

            if len(cropped_binary) > MAX_IMAGE_SIZE:
                logger.error(f"Split image part {i+1} still exceeds size limit: {len(cropped_binary)} bytes")
                raise ValueError("Split image size still exceeds 5MB limit.")
            
            split_binaries.append(cropped_binary)
        
        logger.debug(f"Successfully split image into {len(split_binaries)} parts")
        return split_binaries

    except Exception as e:
        logger.error(f"Error during image splitting: {e}")
        raise ValueError(f"Error during image splitting: {e}")

# --- OpenAI 表記ゆれ補正関数 ---
def unify_text_via_openai(raw_text):
    """
    大幅な表記ゆれがあるテキストを OpenAI の GPT-4 モデルで整形・標準化。
    """
    # API key should already be set in lambda_handler
    if not openai.api_key:
        logger.warning("Warning: OPENAI_API_KEY is not set. Return original text.")
        return raw_text

    logger.debug("raw_text=================================")
    logger.debug(raw_text[:500] + "..." if len(raw_text) > 500 else raw_text)  # Log only first 500 chars to avoid huge logs

    try:
        if not openai.api_key:
            logger.error("OpenAI APIキーが設定されていません。")
            raise ValueError("OpenAI APIキーが設定されていません。")
            
        logger.info("OpenAI GPT-4 APIを呼び出し中...")
        response = openai.chat.completions.create(
            model="gpt-4",
            messages=[
                {
                    "role": "system", 
                    "content": "あなたは請求書データを抽出する専門家です。"
                },
                {
                    "role": "user",
                    "content": f"""与えられた請求書に記載されたテキストを構造的に解釈して、JSON形式に整理してください。
                    ・必須で取得が可能な項目：「発注番号」「金額」「物件名（建物名）」「部屋番号」「工事業者名」
                    ・その他項目は可能であれば取得
                    ・純粋なjson形式のみで回答してください
                    ・内容が重複している情報は不要です
                    ・全角スペース、半角スペースは各項目の値に含めないでください
                    ・テキストから情報が抽出できない場合は空の配列を返してください
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
        logger.info("OpenAI API呼び出し完了")

        cleaned_text = response.choices[0].message.content.strip()

        logger.debug("cleaned_text====================================")
        logger.debug(cleaned_text[:500] + "..." if len(cleaned_text) > 500 else cleaned_text)  # Log only first 500 chars
        return cleaned_text
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return raw_text


# --- PDFテキストから各項目を抽出する関数 ---
def extract_fields_from_text(text):
    """
    テキストから発注番号、金額、物件名、部屋番号、工事業者名を抽出する
    """
    logger.info("JSONデータの抽出開始")
    # JSON部分を抽出
    match = re.search(r'```json\n(\[.*?\])\n```', text, re.DOTALL)
    if match:
        json_data_str = match.group(1)  # Matchオブジェクトから文字列を取得
        logger.debug(f"Found JSON in code block: {json_data_str[:100]}...")
    else:
        json_data_str = text.strip()  # そのままテキストを取得
        logger.debug(f"No JSON code block found, using raw text: {json_data_str[:100]}...")

    try:
        # Print the JSON string for debugging
        logger.debug(f"Attempting to parse JSON: {json_data_str[:200]}...")
        
        invoice_data = json.loads(json_data_str)  # JSON文字列を辞書に変換
        
        # Check if the parsed data is empty
        if not invoice_data:
            logger.warning("Warning: Parsed JSON is empty")
            return []
            
        structured_data = []

        for entry in invoice_data:
            structured_data.append({
                "発注番号": entry.get("発注番号", "不明"),
                "金額": entry.get("金額", "不明"),
                "物件名": entry.get("物件名", "不明"),
                "部屋番号": entry.get("部屋番号", "不明"),
                "工事業者名": entry.get("工事業者名", "不明")
            })

        logger.info(f"Successfully extracted {len(structured_data)} invoice entries")
        return structured_data
    except json.JSONDecodeError as e:
        logger.error(f"JSONの解析に失敗しました: {e}")
        logger.debug(f"JSON文字列: {json_data_str[:200]}...")
        
        # Try to extract JSON from a different format
        try:
            # Sometimes the JSON might be wrapped in different markers
            logger.debug("代替JSONフォーマットを試行中...")
            alt_match = re.search(r'\[(.*?)\]', text, re.DOTALL)
            if alt_match:
                alt_json_str = f"[{alt_match.group(1)}]"
                logger.debug(f"Trying alternative JSON format: {alt_json_str[:100]}...")
                invoice_data = json.loads(alt_json_str)
                
                structured_data = []
                for entry in invoice_data:
                    structured_data.append({
                        "発注番号": entry.get("発注番号", "不明"),
                        "金額": entry.get("金額", "不明"),
                        "物件名": entry.get("物件名", "不明"),
                        "部屋番号": entry.get("部屋番号", "不明"),
                        "工事業者名": entry.get("工事業者名", "不明")
                    })
                
                logger.info(f"Successfully extracted {len(structured_data)} invoice entries using alternative format")
                return structured_data
        except Exception as alt_e:
            logger.error(f"Alternative JSON parsing also failed: {alt_e}")
        
        return []

def parse_invoice_data(text):
    """
    抽出されたデータを14項目にマッピングする
    """
    logger.info("データマッピング処理開始")
    logger.debug(f"入力データ項目数: {len(text)}")
    
    structured_data = []
    for i, entry in enumerate(text):  # pdf_data は extract_fields_from_text の戻り値(list)
        logger.debug(f"データ項目 {i+1} の処理:")
        logger.debug(f"  発注番号: {entry.get('発注番号', '不明')}")
        logger.debug(f"  金額: {entry.get('金額', '不明')}")
        logger.debug(f"  物件名: {entry.get('物件名', '不明')}")
        
        mapped_entry = {
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
        }
        structured_data.append(mapped_entry)
    
    logger.info(f"マッピング完了: {len(structured_data)} 項目")
    return structured_data
