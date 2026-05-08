import pytest
from fastapi.testclient import TestClient
from backend.api.main import app
from backend.db.database import Base, engine, get_db
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Use in-memory SQLite for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine_test = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

Base.metadata.create_all(bind=engine_test)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)

def test_list_documents_empty():
    response = client.get("/api/v1/documents/")
    assert response.status_code == 200
    assert response.json() == []

def test_document_not_found():
    response = client.get("/api/v1/documents/fake-id")
    assert response.status_code == 404
    assert response.json() == {"detail": "Document not found"}

# For testing upload, we'd need a mock image file
# We skip the actual upload test in this simple setup as it requires a valid image for Tesseract to not crash, or mocking Tesseract.
