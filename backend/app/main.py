import uvicorn
from backend.app import create_application

# Create the FastAPI application using the factory
app = create_application()

if __name__ == "__main__":
    # Run the application with uvicorn when script is executed directly
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True) 