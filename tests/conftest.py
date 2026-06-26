"""
Pytest configuration and fixtures for test isolation.

Ensures each test gets a fresh app instance with reset in-memory state.
"""

import pytest
import sys
from importlib import reload


@pytest.fixture(autouse=True)
def reset_app_state():
    """
    Reset app state before each test by reloading the app module.
    This ensures tests don't interfere with each other due to shared in-memory state.
    """
    # Remove app module from cache to force reload
    if "src.app" in sys.modules:
        del sys.modules["src.app"]
    
    # Reload the module to reset the in-memory activities dictionary
    import src.app
    reload(src.app)
    
    yield
    
    # Cleanup after test
    if "src.app" in sys.modules:
        del sys.modules["src.app"]
