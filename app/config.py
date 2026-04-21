from dotenv import load_dotenv
import os
import streamlit as st

def get_env(key: str):
    return os.getenv(key) or st.secrets.get(key)

OPENAI_API_KEY = get_env("OPENAI_API_KEY")
OPENAI_MODEL = get_env("OPENAI_MODEL")

load_dotenv()

TERMENE_API_URL = os.getenv("TERMENE_API_URL")
TERMENE_USERNAME = os.getenv("TERMENE_USERNAME")
TERMENE_PASSWORD = os.getenv("TERMENE_PASSWORD")
TERMENE_SCHEMA_KEY_COMPANY = os.getenv("TERMENE_SCHEMA_KEY_COMPANY")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-5.4")

if not TERMENE_API_URL:
    raise ValueError("Lipsește TERMENE_API_URL din .env")

if not TERMENE_USERNAME:
    raise ValueError("Lipsește TERMENE_USERNAME din .env")

if not TERMENE_PASSWORD:
    raise ValueError("Lipsește TERMENE_PASSWORD din .env")

if not TERMENE_SCHEMA_KEY_COMPANY:
    raise ValueError("Lipsește TERMENE_SCHEMA_KEY_COMPANY din .env")