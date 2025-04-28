"""API layer for the Rizz API application.

This package contains all API-related components including routes, models, and middleware.
"""

from fastapi import APIRouter

# Import and aggregate all routers for easier inclusion in the main app
from backend.app.api.routes.assessment import router as assessment_router
from backend.app.api.routes.chat import router as chat_router
from backend.app.api.routes.scenario import router as scenario_router

# Create a router that includes all other routers
api_router = APIRouter()
api_router.include_router(assessment_router, tags=["conversation"])
api_router.include_router(chat_router, tags=["chat"])
api_router.include_router(scenario_router, tags=["scenario"])
