import os
from typing import Dict, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class Settings:
    PROJECT_NAME: str = "Rizz API"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:3001",
        # Add your production URLs here
    ]

    
    # API Keys
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    GEMINI_API_KEY_EMBEDDING: Optional[str] = os.getenv("GEMINI_API_KEY_EMBEDDING")
    HUGGINGFACE_TOKEN: Optional[str] = os.getenv("HUGGINGFACE_TOKEN")
    DEEPSEEK_API_KEY: Optional[str] = os.getenv("DEEPSEEK_API_KEY")
    
    # Directory settings
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    DOWNLOADS_DIR: str = os.path.join(DATA_DIR, "downloads")
    CHROMA_DB_DIR: str = os.path.join(DATA_DIR, "chroma_db")
    ARCHETYPES_FILE: str = os.path.join(DATA_DIR, "archetypes.json")

    # Vector DB settings
    EMBEDDING_MODEL_NAME: str = "models/embedding-001"  
    BATCH_SIZE: int = 100
    COLLECTION_NAME: str = "transcript_blocks" 
    
    def __init__(self):
        # Create directories if they don't exist
        os.makedirs(self.DOWNLOADS_DIR, exist_ok=True)
        os.makedirs(self.CHROMA_DB_DIR, exist_ok=True)

settings = Settings() 