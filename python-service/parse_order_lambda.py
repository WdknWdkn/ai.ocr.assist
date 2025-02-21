# parse_order_lambda.py (AWS Lambda用サンプル)
import json
import io
import openpyxl
import csv

def lambda_handler(event, context):
    """
    1) S3やBase64等で受け取った CSV/Excel ファイルを解析し、
    2) 14項目 (業者ID, 業者名, 建物名, ... ) のリストを JSON で返す
    """
    # 例: event["file_bytes"] にbase64でファイル内容が入っている想定
    #     event["filename"] に拡張子付きファイル名が入っている想定
    import base64
    file_bytes_b64 = event.get("file_bytes", "")
    filename = event.get("filename", "unknown.csv")

    # デコード
    file_bytes = base64.b64decode(file_bytes_b64)

    # CSV/Excel 判定
    if filename.lower().endswith((".xlsx",".xls")):
        result_data = parse_excel(file_bytes)
    else:
        result_data = parse_csv(file_bytes)

    # JSONで返す
    return {
        "statusCode": 200,
        "body": json.dumps({
            "parsed_orders": result_data
        })
    }

def parse_csv(file_bytes):
    # ここは routes.py の parse_csv をほぼ流用
    result = []
    csv_stream = io.StringIO(file_bytes.decode("utf-8", errors="ignore"))
    reader = csv.DictReader(csv_stream)

    for row in reader:
        row_data = {
            "業者ID":       (row.get("CSV業者ID") or "").strip(),
            "業者名":       (row.get("CSV業者名") or "").strip(),
            "建物名":       (row.get("CSV建物名") or "").strip(),
            "番号":         (row.get("CSV番号")   or "").strip(),
            "受付内容":     (row.get("CSV受付内容") or "").strip(),
            "支払金額":     (row.get("CSV支払金額") or "").strip(),
            "完工日":       (row.get("CSV完工日") or "").strip(),
            "支払日":       (row.get("CSV支払日") or "").strip(),
            "請求日":       (row.get("CSV請求日") or "").strip()
        }
        if row_data["業者ID"]:
            result.append(row_data)
    return result

def parse_excel(file_bytes):
    """
    Excelファイルを openpyxl で解析し、
    10行目までをチェックして1カラム目（列A）が「業者ID」の行をヘッダ行とみなす。
    ヘッダマッチした後は同じ14項目キーをもつ辞書リストを返す。
    """
    result = []
    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), data_only=True)
    sheet = wb.worksheets[0]  # 先頭シートを読む想定

    # 期待されるヘッダ（14項目）
    expected_headers = [
        "業者ID", "業者名", "コード", "建物名", "番号", "受付内容",
        "支払金額", "修繕作成者", "完工日", "修繕業者ID", "支払サイト",
        "支払日", "立替金", "請求日"
    ]

    # 1～10行目をチェック → 1カラム目が「業者ID」の行をヘッダ行とする
    header_row_idx = None
    for row_idx, row in enumerate(sheet.iter_rows(values_only=True), start=1):
        if row_idx > 10:
            break
        if row and len(row) > 0:
            first_col_val = str(row[0]).strip() if row[0] else ""
            if first_col_val == "業者ID":
                header_row_idx = row_idx
                break

    if header_row_idx is None:
        raise ValueError("ヘッダ行が見つかりませんでした(1～10行目の1カラム目に「業者ID」がありません)")

    # ヘッダ行のセル値を読み取り、列Indexを特定
    header_row = list(sheet.iter_rows(min_row=header_row_idx, max_row=header_row_idx, values_only=True))[0]
    headers_map = {}
    for col_idx, val in enumerate(header_row):
        if val is not None:
            val_str = str(val).strip()
            if val_str in expected_headers:
                headers_map[val_str] = col_idx

    # ヘッダ行の次の行からデータ行として読み込み
    for row in sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
        row_data = {}
        for header_name in expected_headers:
            idx = headers_map.get(header_name)
            if idx is not None and idx < len(row):
                cell_val = row[idx] or ""
                row_data[header_name] = str(cell_val).strip()
            else:
                row_data[header_name] = ""

        # 「業者ID」が空ならスキップ
        if not row_data["業者ID"]:
            continue

        result.append(row_data)

    return result
