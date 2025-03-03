class MockOpenAI:
    def chat(self, messages):
        return {"choices": [{"message": {"content": '''[
            {
                "発注番号": "TEST-001",
                "金額": "50000",
                "物件名": "テスト物件",
                "部屋番号": "101",
                "工事業者名": "テスト工事会社"
            }
        ]'''}}]}

    def create(self, *args, **kwargs):
        return self.chat(None)

class Client:
    def __init__(self, api_key=None):
        self.chat = MockOpenAI()
