import datetime
import uuid
from sqlalchemy import Column, String, DateTime, JSON, ForeignKey, Enum
from sqlalchemy.orm import relationship
from backend.db.database import Base
import enum

class DocumentType(str, enum.Enum):
    aadhaar = "aadhaar"
    dl = "dl"
    passport = "passport"
    invoice = "invoice"
    unknown = "unknown"

class DocumentStatus(str, enum.Enum):
    uploaded = "uploaded"
    processing = "processing"
    completed = "completed"
    failed = "failed"

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    filename = Column(String, index=True)
    document_type = Column(String, default=DocumentType.unknown.value)
    status = Column(String, default=DocumentStatus.uploaded.value)
    uploaded_at = Column(DateTime, default=datetime.datetime.utcnow)
    
    extracted_data = relationship("ExtractedData", back_populates="document", uselist=False, cascade="all, delete-orphan")

class ExtractedData(Base):
    __tablename__ = "extracted_data"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()), index=True)
    document_id = Column(String, ForeignKey("documents.id"))
    extracted_text = Column(String)  # Raw OCR text
    parsed_json = Column(JSON)       # LLM structured output
    processed_at = Column(DateTime, default=datetime.datetime.utcnow)

    document = relationship("Document", back_populates="extracted_data")
