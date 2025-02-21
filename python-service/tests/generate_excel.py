import openpyxl

def create_sample_excel():
    wb = openpyxl.Workbook()
    ws = wb.active
    headers = ["業者ID", "業者名", "建物名", "番号", "受付内容", "支払金額", "完工日", "支払日", "請求日"]
    data = ["12345", "テスト工事会社", "サンプルマンション", "101", "修繕工事", "100000", "2025-02-21", "2025-03-21", "2025-02-21"]
    ws.append(headers)
    ws.append(data)
    wb.save("tests/data/sample_orders.xlsx")

if __name__ == "__main__":
    create_sample_excel()
