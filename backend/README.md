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
│   │   │   └── schema.py     # Pydantic models
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
│   │   └── vector_store.py   # Vector database operations 
│   ├── utils/                # Utility functions
│   │   ├── __init__.py
│   │   └── cleaner.py        # Output cleaner for LLM responses
│   └── pipeline/             # Data ingestion&processing pipelines
│   │   ├── __init__.py
│   │   ├── pipeline_start.py
│   │   ├── transcript_to_vector_db.py
│   │   └── url_to_transcript.py
├── data/                     # Data storage
│   ├── prompts/              # Store prompt templates
│   │   └── prompts.py        # Prompt templates 
│   ├── archetypes.json       # Configuration files 
│   ├── chroma_db/            # Vector database storage
│   └── downloads/            # Downloaded data
│   └── log_transcript        # log for ingestion pipeline
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


## Migration Notes

This structure is being set up alongside the existing code for a smooth transition. The migration process will involve:

1. Moving code from the flat structure to the modular structure
2. Updating imports and dependencies
3. Testing the new structure
4. Switching to the new entry point

## Running the Application

```
from root directory:

python -m backend.app.main
```

## Environment Variables

Required environment variables:
- `GEMINI_API_KEY`: API key for Gemini
- `HUGGINGFACE_TOKEN`: Token for HuggingFace
- `DEEPSEEK_API_KEY`: API key for DeepSeek (optional)