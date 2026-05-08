from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from backend.core.config import settings
from backend.core.di import Container
from backend.api.routes import documents
from backend.db.database import init_db
from backend.core.logging import app_logger

def create_app() -> FastAPI:
    # Initialize container
    container = Container()
    
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json"
    )
    
    app.container = container
    
    # Set CORS for Streamlit frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], # In prod, specify the Streamlit URL
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include routers
    app.include_router(documents.router, prefix=f"{settings.API_V1_STR}/documents", tags=["documents"])
    
    @app.on_event("startup")
    def startup_event():
        app_logger.info("Starting up FastAPI application...")
        init_db()
        
    return app

app = create_app()

if __name__ == "__main__":
    uvicorn.run("backend.api.main:app", host="0.0.0.0", port=8000, reload=True)
