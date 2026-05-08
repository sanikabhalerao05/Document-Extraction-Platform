from pydantic import BaseModel
from typing import Optional, Any, Dict
from datetime import datetime

class DocumentBase(BaseModel):
    filename: str
    document_type: str

class DocumentCreate(DocumentBase):
    pass

class DocumentResponse(DocumentBase):
    id: str
    status: str
    uploaded_at: datetime

    class Config:
        from_attributes = True

class ExtractedDataResponse(BaseModel):
    id: str
    document_id: str
    extracted_text: str
    parsed_json: Optional[Dict[str, Any]] = None
    processed_at: datetime

    class Config:
        from_attributes = True

class DocumentDetailsResponse(DocumentResponse):
    extracted_data: Optional[ExtractedDataResponse] = None
