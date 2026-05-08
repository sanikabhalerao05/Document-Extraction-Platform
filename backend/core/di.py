from dependency_injector import containers, providers
from backend.services.ocr_service import OCRService
from backend.services.llm_service import LLMService
from backend.services.extraction_service import ExtractionService

class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(packages=["backend.api.routes"])

    ocr_service = providers.Singleton(OCRService)
    llm_service = providers.Singleton(LLMService)
    
    extraction_service = providers.Factory(
        ExtractionService,
        ocr_service=ocr_service,
        llm_service=llm_service
    )
