"""
Test package for the backend application.

This module contains common utilities, fixtures, and configuration
for testing the ChatMatch backend components.
"""
import os
import json
import asyncio
import pytest
from pathlib import Path

# Paths
TESTS_DIR = Path(__file__).parent
PROJECT_ROOT = Path(__file__).parent.parent
TEST_DATA_DIR = TESTS_DIR / "data"

# Create test data directory if it doesn't exist
os.makedirs(TEST_DATA_DIR, exist_ok=True)

# Common test data
SAMPLE_SCENARIO = {
    "scenario_type": "dating",
    "setting": "party",
    "goal": "first impression",
    "system_archetype": "The Awkward Sweetheart",
    "roast_level": 2,
    "player_sex": "female",
    "system_sex": "male"
}

SAMPLE_MESSAGES = [
    {"role": "user", "content": "Excuse me, have you ever been to tennessee? cuz you're the only ten i see"},
    {"role": "assistant", "content": "lmao, that was a good one, thank you. and yeah, i am actually from tennessee, lol. "},
    {"role": "user", "content": "ok, well i didnt actually thought you were from tennessee, lol. did you come here for the party?"},
    {"role": "assistant", "content": "yeah, i'm here for a weekend. one of the organizer is my best friend so i had to pull up"}
]


# Utility functions
def load_test_json(filename):
    """Load test JSON data from the test data directory."""
    file_path = TEST_DATA_DIR / filename
    if not os.path.exists(file_path):
        return None
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_test_json(data, filename):
    """Save test data as JSON to the test data directory."""
    file_path = TEST_DATA_DIR / filename
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2)
    
    return file_path

# Configure pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "integration: mark a test as an integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark a test as a slow test"
    )
    
# Export utility functions
__all__ = [
    'TESTS_DIR',
    'PROJECT_ROOT',
    'TEST_DATA_DIR',
    'SAMPLE_SCENARIO',
    'SAMPLE_MESSAGES',
    'load_test_json',
    'save_test_json',
] 