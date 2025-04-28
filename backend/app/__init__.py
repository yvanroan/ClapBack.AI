from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.core import settings, get_api_key_or_raise

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for application startup and shutdown.
    This will initialize resources on startup and clean up on shutdown.
    """
    # Startup: Initialize resources
    print("--- Application Starting: Initializing Resources ---")
    
    # Initialize Google Generative AI
    import google.generativeai as genai
    
    try:
        api_key = get_api_key_or_raise("GEMINI_API_KEY")
        genai.configure(api_key=api_key)
        
        # Initialize chat model
        app.state.chat_model = genai.GenerativeModel('gemini-2.0-flash')
        print("Chat Model Initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Chat Model: {e}")
        app.state.chat_model = None
    
    # Initialize embedding model and vector database
    try:
        from backend.app.services.vector_store import initialize_embedding_model, initialize_chroma_client, get_or_create_collection
        
        print("Initializing Embedding Model...")
        app.state.embedding_model = initialize_embedding_model()
        
        print("Initializing ChromaDB Client...")
        app.state.chroma_client = initialize_chroma_client()
        
        print("Getting or Creating Collection...")
        app.state.chroma_collection = get_or_create_collection(app.state.chroma_client)
        
        if app.state.embedding_model and app.state.chroma_collection:
            print("Vector Database Services Initialized Successfully.")
        else:
            print("WARNING: Vector database services not fully initialized.")
    except Exception as e:
        print(f"ERROR: Failed to initialize Vector Database Services: {e}")
        app.state.embedding_model = None
        app.state.chroma_client = None
        app.state.chroma_collection = None
    
    yield
    
    # Shutdown: Clean up resources
    print("--- Application Shutting Down: Cleaning Up Resources ---")
    # Clean up resources if needed
    app.state.chat_model = None
    app.state.embedding_model = None
    
    # Close chroma client if it exists
    if hasattr(app.state, "chroma_client") and app.state.chroma_client:
        try:
            # Proper way to close depends on your implementation
            # app.state.chroma_client.close()
            pass
        except Exception as e:
            print(f"Error closing chroma client: {e}")
    
    app.state.chroma_client = None
    app.state.chroma_collection = None


def create_application() -> FastAPI:
    """
    Factory function to create and configure the FastAPI application.
    """
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description="API for conversation simulation and analysis",
        version="1.0.0",
        lifespan=lifespan
    )
    
    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API router
    from backend.app.api import api_router
    app.include_router(api_router, prefix=settings.API_V1_STR)
    
    @app.get("/")
    async def root():
        """Root endpoint for health check."""
        return {"message": f"Welcome to the {settings.PROJECT_NAME} Backend"}
    
    return app
