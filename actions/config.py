import os
from dotenv import load_dotenv
load_dotenv()

DB_CONFIG = {
    'host': os.getenv("DB_HOST"),
    'user': os.getenv("DB_USER"),
    'password': os.getenv("DB_PASSWORD"),
    'database': os.getenv("DB_NAME"),
    'port': int(os.getenv("DB_PORT", 3306))
}

APP_URL = os.getenv("APP_URL", "http://127.0.0.1:8000")
