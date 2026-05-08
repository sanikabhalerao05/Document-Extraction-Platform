from sqlalchemy.orm import Session
from backend.services.ocr_service import OCRService
from backend.services.llm_service import LLMService
from backend.db.models import Document, ExtractedData, DocumentStatus
from backend.core.logging import app_logger

class ExtractionService:
    def __init__(self, ocr_service: OCRService, llm_service: LLMService):
        self.ocr_service = ocr_service
        self.llm_service = llm_service

    def process_document(self, db: Session, document_id: str, image_bytes: bytes):
        app_logger.info(f"Starting processing for document {document_id}")
        
        # Fetch document
        doc = db.query(Document).filter(Document.id == document_id).first()
        if not doc:
            app_logger.error(f"Document {document_id} not found in DB")
            return

        # Update status to processing
        doc.status = DocumentStatus.processing.value
        db.commit()

        try:
            # Step 1: OCR Extraction
            app_logger.info(f"Extracting text for {document_id}")
            raw_text = self.ocr_service.extract_text(image_bytes, doc.filename)
            
            if not raw_text:
                raise ValueError("No text extracted from image")

            # Step 2: LLM Structured Parsing
            app_logger.info(f"Parsing structured data for {document_id}")
            parsed_json = self.llm_service.extract_structured_data(raw_text, doc.document_type)
            
            # Step 2.5: Generate Structured Data
            # Note: raw_text is already filtered for English-only content by OCRService

            # Step 3: Save to Database (Maximum English Data)
            app_logger.info(f"Saving extracted data for {document_id}")
            extracted_data = ExtractedData(
                document_id=doc.id,
                extracted_text=raw_text, # Captures all English text found
                parsed_json=parsed_json
            )
            db.add(extracted_data)
            
            # Update Document Status
            doc.status = DocumentStatus.completed.value
            db.commit()
            app_logger.info(f"Successfully processed document {document_id}")

        except Exception as e:
            app_logger.exception(f"Failed to process document {document_id}: {str(e)}")
            doc.status = DocumentStatus.failed.value
            db.commit()
