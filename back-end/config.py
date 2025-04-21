import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# OpenAI API 설정
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_MODEL = "text-embedding-ada-002"
OPENAI_MODEL = "gpt-3.5-turbo"

# 문서 및 데이터베이스 경로 설정
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_PATH = os.path.join(BASE_DIR, "data", "docs")
VECTOR_DB_PATH = os.path.join(BASE_DIR, "data", "vector_db")

# docs 디렉토리가 없으면 생성
if not os.path.exists(DOCS_PATH):
    os.makedirs(DOCS_PATH)

# vector_db 디렉토리가 없으면 생성
if not os.path.exists(VECTOR_DB_PATH):
    os.makedirs(VECTOR_DB_PATH)
