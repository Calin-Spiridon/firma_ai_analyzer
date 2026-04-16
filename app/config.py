from dotenv import load_dotenv
import os

load_dotenv()

TERMENE_API_URL = os.getenv("TERMENE_API_URL")
TERMENE_USERNAME = os.getenv("TERMENE_USERNAME")
TERMENE_PASSWORD = os.getenv("TERMENE_PASSWORD")
TERMENE_SCHEMA_KEY_COMPANY = os.getenv("TERMENE_SCHEMA_KEY_COMPANY")

if not TERMENE_API_URL:
    raise ValueError("Lipsește TERMENE_API_URL din .env")

if not TERMENE_USERNAME:
    raise ValueError("Lipsește TERMENE_USERNAME din .env")

if not TERMENE_PASSWORD:
    raise ValueError("Lipsește TERMENE_PASSWORD din .env")

if not TERMENE_SCHEMA_KEY_COMPANY:
    raise ValueError("Lipsește TERMENE_SCHEMA_KEY_COMPANY din .env")