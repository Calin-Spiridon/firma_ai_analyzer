from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.chat.completions.create(
    model=os.getenv("OPENAI_MODEL", "gpt-4o"),
    messages=[{"role": "user", "content": "Spune doar: conexiune reușită."}]
)

print(response.choices[0].message.content)
