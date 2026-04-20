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
            "Content-Type": "application/json",
        }
        self.timeout = 30

    def _post(self, payload: dict) -> dict:
        try:
            response = requests.post(
                self.url,
                headers=self.headers,
                json=payload,
                auth=self.auth,
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise Exception(f"Eroare de conexiune la Termene API: {str(exc)}") from exc

        if response.status_code != 200:
            raise Exception(
                f"Eroare Termene API: {response.status_code} - {response.text}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise Exception("Răspuns invalid de la Termene API: JSON imposibil de parsat.") from exc

    def fetch_schema(self, cui: int, schema_key: str) -> dict:
        payload = {
            "cui": int(cui),
            "schemaKey": schema_key,
        }
        return self._post(payload)

    def raw_post(self, payload: dict) -> dict:
        """
        Trimite orice payload dict către API-ul Termene.
        Îl folosim ca tester până descoperim payload-ul exact de search.
        """
        return self._post(payload)