"""Core module for application-wide settings, security, and utilities.

This module contains foundational components used throughout the application:
- Configuration and settings management
- Security utilities including API key validation
- Base utilities and helpers

Directly importing from this package (e.g., `from backend.app.core import settings`)
is the preferred way to access these components.
"""

# Export key components for easier imports throughout the application
from backend.app.core.config import settings
from backend.app.core.security import get_api_key_or_raise, validate_api_keys

# Version information
__version__ = "1.0.0"
