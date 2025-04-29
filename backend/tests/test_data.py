"""
Tests for the data module functionality.
"""
import pytest
import asyncio
import os
from backend.data import (
    load_archetypes,
    load_archetypes_async,
    ARCHETYPES_FILE
)
from backend.app.services import load_archetypes_data

def test_archetypes_file_exists():
    """Test that the archetypes file exists."""
    assert os.path.exists(ARCHETYPES_FILE)
    assert os.path.isfile(ARCHETYPES_FILE)

def test_load_archetypes_sync():
    """Test the synchronous archetype loading function."""
    archetypes = load_archetypes()
    
    # Verify the structure
    assert isinstance(archetypes, dict)
    assert len(archetypes) > 0
    
    # Check for expected keys
    assert "system_archetypes" in archetypes
    assert "user_archetypes" in archetypes
    assert "conversation_aspects" in archetypes
    
    # Check that there are archetypes defined
    assert len(archetypes["system_archetypes"]) > 0
    assert len(archetypes["user_archetypes"]) > 0
    assert len(archetypes["conversation_aspects"]) > 0

@pytest.mark.asyncio
async def test_load_archetypes_async():
    """Test the asynchronous archetype loading function."""
    archetypes = await load_archetypes_async()
    
    # Verify the structure
    assert isinstance(archetypes, dict)
    assert len(archetypes) > 0
    
    # Check for expected keys
    assert "system_archetypes" in archetypes
    assert "user_archetypes" in archetypes
    assert "conversation_aspects" in archetypes

@pytest.mark.asyncio
async def test_service_archetypes_loader():
    """Test the service's archetype loading function."""
    archetypes = await load_archetypes_data()
    
    # Verify the structure
    assert isinstance(archetypes, dict)
    assert len(archetypes) > 0
    
    # Check for expected keys
    assert "system_archetypes" in archetypes
    assert "user_archetypes" in archetypes
    assert "conversation_aspects" in archetypes
    
    # Ensure both loading methods return the same data
    sync_archetypes = load_archetypes()
    assert archetypes.keys() == sync_archetypes.keys()
    
    # Check some sample values to confirm they're identical
    for key in ["system_archetypes", "user_archetypes"]:
        assert len(archetypes[key]) == len(sync_archetypes[key]) 