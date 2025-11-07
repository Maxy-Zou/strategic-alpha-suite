"""Shared pytest fixtures for Dashboard tests."""

import sys
from pathlib import Path

# Add src and app directories to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
app_path = project_root / "app"

for path in [src_path, app_path]:
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

# Also add backend src to path
backend_src = project_root.parent / "strategic_alpha" / "src"
if str(backend_src) not in sys.path:
    sys.path.insert(0, str(backend_src))

import pytest
from datetime import datetime
from typing import Dict, Any


@pytest.fixture
def sample_session_id() -> str:
    """Sample session ID for testing."""
    return "test_session_12345"


@pytest.fixture
def sample_ticker() -> str:
    """Sample ticker symbol."""
    return "NVDA"


@pytest.fixture
def mock_streamlit_secrets(monkeypatch):
    """Mock Streamlit secrets for testing."""
    class MockSecrets:
        def get(self, key, default=None):
            secrets = {
                'FRED_API_KEY': 'test_fred_key',
                'SEC_API_KEY': 'test_sec_key',
            }
            return secrets.get(key, default)

        def __getitem__(self, key):
            return self.get(key)

    monkeypatch.setattr('streamlit.secrets', MockSecrets())
    return MockSecrets()
