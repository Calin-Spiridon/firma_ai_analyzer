from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model=os.getenv("OPENAI_MODEL", "gpt-5.4"),
    input="Spune doar: conexiune reușită."
)

print(response.output_text)