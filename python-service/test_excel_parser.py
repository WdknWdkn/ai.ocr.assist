#!/usr/bin/env python3
import sys
from parse_order_lambda import parse_excel
import openpyxl
from io import BytesIO

# Create a test Excel file
wb = openpyxl.Workbook()
ws = wb.active

# Add title row
ws.cell(row=1, column=1, value="会社別発注リスト（完工日：2024/12）")

# Add headers (row 2)
headers = ['業者ID', '業者名', '建物名', '番号', '受付内容', '支払金額', '完工日', '支払日', '請求日']
for col, header in enumerate(headers, 1):
    ws.cell(row=2, column=col, value=header)

# Add test data
test_data = [
    [1001, 'テスト業者1', 'テストビル1', 1, '修繕内容1', 10000, '2024-12-01', '2024-12-31', '2024-12-15'],
    [1002, 'テスト業者2', 'テストビル2', 2, '修繕内容2', 20000, '2024-12-02', '2024-12-31', '2024-12-15']
]
for row_idx, row_data in enumerate(test_data, 3):
    for col_idx, value in enumerate(row_data, 1):
        ws.cell(row=row_idx, column=col_idx, value=value)

# Save to BytesIO
excel_bytes = BytesIO()
wb.save(excel_bytes)
excel_bytes.seek(0)

# Test parsing
try:
    result = parse_excel(excel_bytes.getvalue())
    print('Parsed result:')
    import json
    print(json.dumps(result, ensure_ascii=False, indent=2))
except Exception as e:
    print(f'Error: {str(e)}')
