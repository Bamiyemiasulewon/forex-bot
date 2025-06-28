import httpx
import os
import logging
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

class ApiService:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        if not self.base_url:
            logger.critical("API_BASE_URL is not configured. The bot will not be ableto fetch data.")
            # In a real scenario, you might want to raise an exception or handle this more gracefully
            raise ValueError("API_BASE_URL cannot be empty.")

    async def make_api_call(self, endpoint: str, method: str = "GET", **kwargs) -> Optional[Dict[str, Any]]:
        """
        Makes an asynchronous API call to the backend.

        Args:
            endpoint: The API endpoint to call (e.g., '/signals').
            method: HTTP method (GET, POST, etc.).
            **kwargs: Additional arguments for httpx.request (e.g., params, json).

        Returns:
            A dictionary with the JSON response or None if an error occurred.
        """
        url = f"{self.base_url}{endpoint}"
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                logger.info(f"Making API call: {method} {url} with params {kwargs.get('params')}")
                response = await client.request(method, url, **kwargs)
                response.raise_for_status()  # Raise an exception for 4xx or 5xx status codes
                return response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"API Error: Received status {e.response.status_code} for {url}. Response: {e.response.text}")
            # You could return the error message to the user
            # return {"error": f"API returned an error: {e.response.status_code}"}
        except httpx.TimeoutException:
            logger.error(f"API Timeout: The request to {url} timed out.")
            # return {"error": "The request to the server timed out. Please try again."}
        except httpx.ConnectError as e:
            logger.error(f"Connection Error: Cannot connect to {url}. Local server may not be running.")
            # return {"error": "Cannot connect to local server. Please start the server first."}
        except httpx.RequestError as e:
            logger.error(f"Request Error: An error occurred while requesting {url}. Details: {e}")
        except Exception as e:
            logger.error(f"An unexpected error occurred during the API call: {e}", exc_info=True)
        
        return None

# Initialize with an environment variable, providing a default for local development
# The RENDER_EXTERNAL_URL is provided by Render, so we can use it to construct the API URL
API_BASE_URL = os.getenv("RENDER_EXTERNAL_URL", "http://127.0.0.1:8001")
api_service = ApiService(base_url=API_BASE_URL) 