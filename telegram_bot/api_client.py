import httpx
import json
from pathlib import Path
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type

class ApiClient:
    """Client for interacting with the AI Core API."""

    def __init__(self, base_url: str):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=120.0)

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ingest_text(self, text: str, source: str = "telegram", **kwargs):
        """Sends text to the ingestion endpoint."""
        url = f"{self.base_url}/ingest"
        
        # API expects multipart/form-data with 'metadata' as JSON string
        metadata = {"source": source, "type": "text", **kwargs}
        data = {
            "text": text,
            "metadata": json.dumps(metadata)
        }
        
        # httpx handles multipart/form-data when 'data' is used
        response = await self.client.post(url, data=data)
        response.raise_for_status()
        return response.json()
    
    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def chat_message(self, payload: dict):
        """Send a chat message to orchestrator via gateway."""
        url = f"{self.base_url}/chat/message"
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ingest_file(self, file_path: str, source: str = "telegram", **kwargs):
        """Sends a file to the ingestion endpoint."""
        url = f"{self.base_url}/ingest"
        
        metadata = {"source": source, "type": "file", **kwargs}
        data = {
            "metadata": json.dumps(metadata)
        }
        
        # Open the file in binary mode
        with open(file_path, "rb") as f:
            files = {"file": (Path(file_path).name, f)}
            response = await self.client.post(url, data=data, files=files)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def summarize(self, chat_id: int, **kwargs):
        """Calls the summarize endpoint."""
        url = f"{self.base_url}/summarize"
        payload = {"chat_id": chat_id, **kwargs}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(2), retry=retry_if_exception_type(httpx.RequestError))
    async def ask(self, question: str, chat_id: int):
        """Calls the ask endpoint."""
        url = f"{self.base_url}/ask"
        payload = {"query": question, "chat_id": str(chat_id)}
        response = await self.client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
    
    async def close(self):
        await self.client.aclose()
