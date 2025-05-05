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
        #this initializes both the gemini and the embedding
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
        from backend.app.services.vector_store import initialize_qdrant_client, get_or_create_collection
        
        print("Initializing Qdrant Client...")
        app.state.qdrant_client = initialize_qdrant_client()
        
        if app.state.qdrant_client:
            print("Initializing Qdrant Collection...")
            app.state.collection_name = get_or_create_collection(app.state.qdrant_client)
            print(f"Qdrant initialization complete: {app.state.collection_name}")
        else:
            print("Warning: Failed to initialize Qdrant client")
            app.state.qdrant_client = None
            app.state.collection_name = None
    except Exception as e:
        print(f"Error during Qdrant initialization: {e}")
        app.state.qdrant_client = None
        app.state.collection_name = None
    
    yield
    
    # Shutdown: Clean up resources
    print("--- Application Shutting Down: Cleaning Up Resources ---")
    # Clean up resources if needed
    app.state.chat_model = None
    
    # Close qdrant client if it exists
    if hasattr(app.state, "qdrant_client") and app.state.qdrant_client:
        try:
            # Nothing to close for Qdrant HTTP client
            app.state.qdrant_client = None
            app.state.collection_name = None
            print("Qdrant resources cleaned up.")
        except Exception as e:
            print(f"Error closing Qdrant client: {e}")
    
    app.state.qdrant_client = None
    app.state.collection_name = None


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
    
    @app.api_route("/", methods=["GET", "HEAD"], include_in_schema=False)
    async def root():
        """Root endpoint for health check."""
        return {"message": f"Welcome to the {settings.PROJECT_NAME} Backend"}
    
    return app
