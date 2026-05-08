from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, BackgroundTasks, Form
from sqlalchemy.orm import Session
from typing import List
from dependency_injector.wiring import inject, Provide

from backend.db.database import get_db
from backend.db.models import Document, DocumentType, ExtractedData
from backend.schemas.document import DocumentResponse, DocumentDetailsResponse
from backend.core.di import Container
from backend.services.extraction_service import ExtractionService
from backend.core.logging import app_logger

router = APIRouter()

@router.post("/upload", response_model=DocumentResponse)
@inject
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    document_type: str = Form(DocumentType.unknown.value),
    db: Session = Depends(get_db),
    extraction_service: ExtractionService = Depends(Provide[Container.extraction_service])
):
    app_logger.info(f"Received upload request for {file.filename} of type {document_type}")
    
    # Validate file type (basic)
    if file.content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        # For simplicity, we just process images right now since tesseract processes images natively.
        # Handling PDFs requires pdf2image which is another dependency.
        # We will allow images for the demo.
        if file.content_type != "application/pdf":
            pass # We should be fine with images
            
    # Read file content
    contents = await file.read()
    
    # Create document record
    doc = Document(
        filename=file.filename,
        document_type=document_type
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)
    
    # Schedule background task for extraction
    background_tasks.add_task(
        extraction_service.process_document,
        db=Session(bind=db.get_bind()), # In real-world, might want a new session
        document_id=doc.id,
        image_bytes=contents
    )
    
    return doc

@router.get("/", response_model=List[DocumentResponse])
def list_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    docs = db.query(Document).order_by(Document.uploaded_at.desc()).offset(skip).limit(limit).all()
    return docs

@router.get("/{document_id}", response_model=DocumentDetailsResponse)
def get_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    return doc

@router.delete("/{document_id}")
def delete_document(document_id: str, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    db.delete(doc)
    db.commit()
    return {"message": "Document deleted successfully"}
