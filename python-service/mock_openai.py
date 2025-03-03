class MockOpenAI:
    def chat(self, messages):
        return {"choices": [{"message": {"content": '''{"message": "請求書の解析が完了しました。", "invoice_data": [
            {
                "請求書番号": "TEST-001",
                "発行日": "2025-01-01",
                "請求金額": "10000",
                "取引先名": "テスト株式会社",
                "支払期限": "2025-01-31",
                "備考": "テストデータ"
            }
        ], "text": "請求書のテストデータです"}'''}}]}

    def create(self, *args, **kwargs):
        return self.chat(None)

class Client:
    def __init__(self, api_key=None):
        self.chat = MockOpenAI()
