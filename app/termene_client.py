import json
import requests

from app.config import (
    TERMENE_API_URL,
    TERMENE_USERNAME,
    TERMENE_PASSWORD,
)


class TermeneClient:
    def __init__(self):
        self.url = TERMENE_API_URL
        self.auth = (TERMENE_USERNAME, TERMENE_PASSWORD)
        self.headers = {
            "Content-Type": "application/json"
        }

    def fetch_schema(self, cui: int, schema_key: str) -> dict:
        payload = json.dumps({
            "cui": cui,
            "schemaKey": schema_key
        })

        response = requests.post(
            self.url,
            headers=self.headers,
            data=payload,
            auth=self.auth,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(
                f"Eroare Termene API: {response.status_code} - {response.text}"
            )

        return response.json()