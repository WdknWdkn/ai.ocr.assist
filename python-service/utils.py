import os
from dotenv import load_dotenv
from fastapi import HTTPException
import openai

load_dotenv()

MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

def validate_file_size(file_size: int, max_size: int = MAX_FILE_SIZE):
    if file_size > max_size:
        raise HTTPException(status_code=413, detail="File too large")

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not configured")
    return openai.Client(api_key=api_key)
