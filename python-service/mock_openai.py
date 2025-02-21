class MockOpenAI:
    def chat(self, messages):
        return {"choices": [{"message": {"content": "Mock OCR result"}}]}

    def create(self, *args, **kwargs):
        return {"choices": [{"message": {"content": "Mock OCR result"}}]}

class Client:
    def __init__(self, api_key=None):
        self.chat = MockOpenAI()
