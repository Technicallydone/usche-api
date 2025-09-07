import requests
import json
import base64
from typing import List, Optional, Dict

from usche_app import settings

class BeemSMSClient:
    def __init__(self):
        self.source_addr = settings.BEEM_SENDER_ID
        self.base_url = settings.BEEM_BASE_URL
        self.auth_token = self._encode_credentials(settings.BEEM_API_KEY, settings.BEEM_SECRET_KEY)
        self.headers = {
            "Content-Type": "application/json",
            "Authorization": f"Basic {self.auth_token}"
        }

    def _encode_credentials(self, api_key: str, secret_key: str) -> str:
        credentials = f"{api_key}:{secret_key}"
        return base64.b64encode(credentials.encode()).decode()

    def send_sms(
        self,
        message: str,
        recipients: List[str],
        encoding: str = "0",
        schedule_time: Optional[str] = ""
    ) -> Dict:
        recipient_data = [
            {"recipient_id": idx + 1, "dest_addr": phone}
            for idx, phone in enumerate(recipients)
        ]

        payload = {
            "source_addr": self.source_addr,
            "schedule_time": schedule_time,
            "encoding": encoding,
            "message": message,
            "recipients": recipient_data
        }

        try:
            response = requests.post(
                self.base_url,
                headers=self.headers,
                data=json.dumps(payload)
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {
                "successful": False,
                "error": str(e)
            }
