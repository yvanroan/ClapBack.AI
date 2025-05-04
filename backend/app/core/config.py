import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pathlib import Path

#BaseSettings gets the .env values for ya
class Settings(BaseSettings):
    PROJECT_NAME: str = "Rizz API"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        # "http://localhost:3000",
        # "http://localhost:3001",
        "*"
    ]

    
    # API Keys
    GEMINI_API_KEY: str
    HUGGINGFACE_TOKEN: str 
    DEEPSEEK_API_KEY: str 
    
    # Directory settings
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    DOWNLOADS_DIR: str = os.path.join(DATA_DIR, "downloads")
    CHROMA_DB_DIR: str = os.path.join(DATA_DIR, "chroma_db")
    ARCHETYPES_FILE: str = os.path.join(DATA_DIR, "archetypes.json")

    # Vector DB settings
    EMBEDDING_MODEL_NAME: str = "models/embedding-001"  
    BATCH_SIZE: int = 100
    COLLECTION_NAME: str = "transcript_blocks" 
    
    def create_dir(self):
        # Create directories after the model is fully initialized
        os.makedirs(self.DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_DB_DIR, exist_ok=True)

    class Config:
        env_file = Path(__file__).resolve().parents[3] / ".env"

settings = Settings() 
settings.create_dir()