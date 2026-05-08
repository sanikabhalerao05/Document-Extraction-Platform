import httpx
from typing import Dict, Any, List

class APIClient:
    def __init__(self, base_url: str = "http://localhost:8000/api/v1"):
        self.base_url = base_url

    def upload_document(self, file_path: str, document_type: str) -> Dict[str, Any]:
        url = f"{self.base_url}/documents/upload"
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        mime_type = mime_type or "application/octet-stream"
        
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f, mime_type)}
            data = {"document_type": document_type}
            response = httpx.post(url, files=files, data=data, timeout=30.0)
            response.raise_for_status()
            return response.json()

    def get_documents(self, limit: int = 100) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/documents/?limit={limit}"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def get_document_details(self, document_id: str) -> Dict[str, Any]:
        url = f"{self.base_url}/documents/{document_id}"
        response = httpx.get(url, timeout=10.0)
        response.raise_for_status()
        return response.json()

    def delete_document(self, document_id: str) -> bool:
        url = f"{self.base_url}/documents/{document_id}"
        response = httpx.delete(url, timeout=10.0)
        response.raise_for_status()
        return True
