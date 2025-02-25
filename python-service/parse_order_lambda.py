#!/usr/bin/env python3
import json
import io
import os
import sys
import csv
import traceback
import openpyxl
from io import BytesIO

def parse_csv(file_bytes):
    """Parse CSV file content and return list of orders"""
    try:
        content = file_bytes.decode("utf-8", errors="ignore")
        if content.startswith('\ufeff'):
            content = content[1:]
            
        csv_stream = io.StringIO(content)
        reader = csv.DictReader(csv_stream)
        
        result = []
        for row in reader:
            row_data = {}
            for key in ['業者ID', '業者名', '建物名', '番号', '受付内容', '支払金額', '完工日', '支払日', '請求日']:
                raw_value = row.get(key, '').strip()
                
                if key in ['業者ID', '番号', '支払金額']:
                    try:
                        row_data[key] = int(float(raw_value))
                    except (ValueError, TypeError):
                        raise ValueError(f"数値項目「{key}」の形式が正しくありません。")
                else:
                    row_data[key] = raw_value
            
            if row_data["業者ID"]:
                result.append(row_data)
        
        return result
    except Exception as e:
        print(f"Error parsing CSV: {str(e)}", file=sys.stderr)
        raise

def parse_excel(file_bytes):
    """Parse Excel file content and return list of orders"""
    try:
        wb = openpyxl.load_workbook(BytesIO(file_bytes), data_only=True)
        sheet = wb.worksheets[0]  # 先頭シートを読む想定

        # ヘッダ行を探す（1～10行目）
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

        # ヘッダ行の列インデックスを取得
        header_row = list(sheet.iter_rows(min_row=header_row_idx, max_row=header_row_idx, values_only=True))[0]
        headers_map = {}
        for col_idx, val in enumerate(header_row):
            if val is not None:
                val_str = str(val).strip()
                headers_map[val_str] = col_idx

        # データ行を読み込み
        result = []
        for row in sheet.iter_rows(min_row=header_row_idx + 1, values_only=True):
            row_data = {}
            for key in ['業者ID', '業者名', '建物名', '番号', '受付内容', '支払金額', '完工日', '支払日', '請求日']:
                idx = headers_map.get(key)
                if idx is not None and idx < len(row):
                    raw_value = str(row[idx] or '').strip()
                    
                    if key in ['業者ID', '番号', '支払金額']:
                        try:
                            row_data[key] = int(float(raw_value))
                        except (ValueError, TypeError):
                            raise ValueError(f"数値項目「{key}」の形式が正しくありません。")
                    else:
                        row_data[key] = raw_value
                else:
                    row_data[key] = ''

            if row_data["業者ID"]:
                result.append(row_data)

        return result
    except Exception as e:
        print(f"Error parsing Excel: {str(e)}", file=sys.stderr)
        raise

if __name__ == "__main__":
    print("This module is now used as a library and should not be run directly.")
