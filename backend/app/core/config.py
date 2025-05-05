import os
from typing import Dict, List, Optional
from pydantic_settings import BaseSettings
from pathlib import Path
from pydantic import model_validator, Field

# BaseSettings gets the .env values for ya
class Settings(BaseSettings):
    PROJECT_NAME: str = "Rizz API"
    API_V1_STR: str = "/api/v1"
    
    # CORS
    BACKEND_CORS_ORIGINS: List[str] = []
    
    # API Keys
    GEMINI_API_KEY: str
    HUGGINGFACE_TOKEN: str 
    FRONTEND_URL: str
    
    # Qdrant settings - making them optional with default values
    QDRANT_URL: Optional[str] = ""
    QDRANT_API_KEY: Optional[str] = ""
    
    # AWS settings - defining them as Fields with default None to allow them in the model
    aws_access_key_id: Optional[str] = Field(None, exclude=True)
    aws_secret_access_key: Optional[str] = Field(None, exclude=True)
    developer_group_aws_access_key_id: Optional[str] = Field(None, exclude=True)
    developer_group_aws_secret_access_key: Optional[str] = Field(None, exclude=True)
    aws_region: Optional[str] = Field(None, exclude=True)
    aws_account: Optional[str] = Field(None, exclude=True)
    aws_bucket_name: Optional[str] = Field(None, exclude=True)

    # Directory settings
    DATA_DIR: str = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data")
    DOWNLOADS_DIR: str = os.path.join(DATA_DIR, "downloads")
    ARCHETYPES_FILE: str = os.path.join(DATA_DIR, "archetypes.json")

    # Vector DB settings
    EMBEDDING_MODEL_NAME: str = "models/embedding-001"  
    BATCH_SIZE: int = 100
    COLLECTION_NAME: str = "transcript_blocks" 
    EMBEDDING_DIMENSION: int = 768
    
    @model_validator(mode='before')
    @classmethod
    def assemble_cors(cls, values):
        if isinstance(values, dict):
            frontend_url = values.get("FRONTEND_URL")
            default_cors = ["http://localhost:3000", "http://localhost:3001"]
            if frontend_url:
                values["BACKEND_CORS_ORIGINS"] = [frontend_url] + default_cors
            else:
                values["BACKEND_CORS_ORIGINS"] = default_cors
        return values

    def create_dir(self):
        # Create directories after the model is fully initialized
        os.makedirs(self.DOWNLOADS_DIR, exist_ok=True)
        
    class Config:
        env_file = Path(__file__).resolve().parents[3] / ".env"
        extra = "allow"  # Allow extra fields that aren't defined in the model

settings = Settings() 
settings.create_dir()