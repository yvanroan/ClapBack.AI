# Rizz API Backend

## Project Structure

```
backend/
├── app/                      # Main application package
│   ├── __init__.py           # Application factory and root router setup
│   ├── main.py               # New application entry point
│   ├── api/                  # API layer
│   │   ├── __init__.py
│   │   ├── models/           # API request/response models
│   │   │   └── schema.py     # Pydantic models (also exists at root)
│   │   ├── middleware/       # API middleware (empty)
│   │   ├── routes/           # Endpoint routes
│   │   │   ├── __init__.py
│   │   │   ├── chat.py
│   │   │   ├── scenario.py
│   │   │   └── assessment.py
│   │   └── endpoints/        # Specific endpoint logic (contains assessment.py)
│   │       └── assessment.py
│   ├── core/                 # Core application settings
│   │   ├── __init__.py
│   │   ├── config.py         # Configuration handling
│   │   └── security.py       # Security features
│   ├── services/             # Business logic services
│   │   ├── __init__.py
│   │   ├── llm/              # LLM-related services
│   │   │   ├── __init__.py
│   │   │   └── gemini.py     # Gemini-specific code
│   │   ├── assessments.py    # Assessment creation logic
│   │   ├── chat.py           # Chat service logic
│   │   ├── scenarios.py      # Scenario management
│   │   ├── vector_service.py # Vector DB service interaction
│   │   └── vector_store.py   # Vector database operations (also exists at root)
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   └── cleaner.py        # Output cleaner for LLM responses (also exists at root)
│   └── pipeline/             # Data processing pipelines (empty)
├── data/                     # Data storage
│   ├── prompts/              # Store prompt templates
│   │   └── prompts.py        # Prompt templates (also exists at root)
│   ├── archetypes.json       # Configuration files (also exists at root)
│   ├── chroma_db/            # Vector database storage
│   └── downloads/            # Downloaded data
├── tests/                    # Test suite
│   ├── __init__.py
│   ├── conftest.py
│   ├── pytest.ini
│   ├── README.md
│   ├── data/
│   │   └── .gitkeep
│   ├── test_api.py
│   ├── test_app_initialization.py
│   ├── test_assessment.py
│   ├── test_chat.py
│   ├── test_conversation_edge_cases.py
│   ├── test_data.py
│   ├── test_llm.py
│   ├── test_scenarios.py
│   ├── test_security_edge_cases.py
│   ├── test_vector_edge_cases.py
│   └── test_vector_service.py
├── reels.txt                 # Input reels for scripts?
├── logs.json                 # Application logs for the data pipeline
├── requirements.txt          # Dependencies
└── .env                      # Environment variables
```
some extra file that are undergoing migration
```
├── downloads/                # Downloaded data (duplicate)
├── main.py                   # Original entry point (partially migrated)
├── back.py                   # entry point of the data pipeline
├── cleaner.py                # Utility - duplicate in app/utils/
├── youtube_to_vectordb.py    # Script for populating vector DB 
├── merge_scenario.py         # Script for merging scenarios to tagged data
├── tagging_processor.py      # Script for adding tags to the data
├── prompts.py                # Prompts - duplicate in data/prompts/
├── schema.py                 # Pydantic models - duplicate in app/api/models/
├── vector_store.py           # Vector store logic - duplicate in app/services/
└── archetypes.json           # Config - duplicate in data/
```

## Migration Notes

This structure is being set up alongside the existing code for a smooth transition. The migration process will involve:

1. Moving code from the flat structure to the modular structure
2. Updating imports and dependencies
3. Testing the new structure
4. Switching to the new entry point

## Running the Application

**Current (original) version:**
```
cd backend
python main.py
```

**New structured version (once migration is complete):**
```
from root directory:

python -m backend.app.main
```

## Environment Variables

Required environment variables:
- `GEMINI_API_KEY`: API key for Gemini
- `GEMINI_API_KEY_EMBEDDING`: API key for Gemini embeddings
- `HUGGINGFACE_TOKEN`: Token for HuggingFace
- `DEEPSEEK_API_KEY`: API key for DeepSeek (optional)