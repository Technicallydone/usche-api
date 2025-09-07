import requests
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class HTTPClient:
    """
    A reusable HTTP client for making HTTP requests, including support for HTTPS with certificates.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_path: Optional[str] = None
    ):
        """
        Initializes the HTTP client.

        Args:
            base_url (Optional[str]): The base URL for API requests.
            headers (Optional[Dict[str, str]]): Default headers for requests.
            cert_path (Optional[str]): Path to SSL certificate.
            key_path (Optional[str]): Path to SSL key.
            ca_path (Optional[str]): Path to CA certificate.
        """
        self.base_url = base_url if base_url else ""
        self.headers = headers or {}
        self.cert = (cert_path, key_path) if cert_path and key_path else None
        self.verify = ca_path if ca_path else True

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
    def request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """
        Makes an HTTP request and returns the full response object.

        Args:
            method (str): HTTP method (GET, POST, PUT, PATCH, DELETE, etc.).
            endpoint (str): API endpoint.
            kwargs: Additional request parameters like headers, json, data, params, etc.

        Returns:
            requests.Response: The full response object.
        """
        url = f"{self.base_url.rstrip('/')}/{endpoint}" if endpoint else self.base_url

        headers = {**self.headers, **kwargs.pop("headers", {})}
        
        try:
            response = requests.request(
                method,
                url,
                headers=headers,
                cert=self.cert,
                verify=self.verify,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"HTTP request failed: {e}", exc_info=True)
            return None

    def get(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("GET", endpoint, **kwargs)
    
    def post(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("POST", endpoint, **kwargs)
    
    def put(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PUT", endpoint, **kwargs)
    
    def patch(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("PATCH", endpoint, **kwargs)
    
    def delete(self, endpoint: str, **kwargs) -> requests.Response:
        return self.request("DELETE", endpoint, **kwargs)
