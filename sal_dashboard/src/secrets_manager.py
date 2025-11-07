"""
Secrets management for Streamlit deployment.

Provides integration with Streamlit secrets and environment variable fallback.
"""

from __future__ import annotations

import os
from typing import Any, Optional

try:
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError:
    STREAMLIT_AVAILABLE = False


def get_secret(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Get a secret from Streamlit secrets or environment variable.
    
    Priority:
    1. Streamlit secrets (for deployed apps)
    2. Environment variable
    3. Default value
    
    Args:
        key: Secret key name
        default: Default value if not found
        
    Returns:
        Secret value or default
    """
    # Try Streamlit secrets first (for deployed apps)
    if STREAMLIT_AVAILABLE:
        try:
            if hasattr(st, "secrets") and key in st.secrets:
                return st.secrets[key]
        except Exception:
            # Secrets not available (e.g., not in Streamlit context)
            pass
    
    # Fallback to environment variable
    return os.getenv(key, default)


def get_secret_required(key: str, description: str = "") -> str:
    """
    Get a required secret, raising an error if not found.
    
    Args:
        key: Secret key name
        description: Description of what the secret is for (for error message)
        
    Returns:
        Secret value
        
    Raises:
        ValueError: If secret is not found
    """
    value = get_secret(key)
    if value is None or value == "":
        msg = f"Required secret '{key}' not found."
        if description:
            msg += f" {description}"
        msg += (
            "\n\nFor local development, set it in .env file or environment variable."
            "\nFor deployment, add it to Streamlit secrets."
        )
        raise ValueError(msg)
    return value


def validate_secrets(required_keys: list[str]) -> dict[str, bool]:
    """
    Validate that required secrets are available.
    
    Args:
        required_keys: List of required secret keys
        
    Returns:
        Dictionary mapping key to availability status
    """
    status = {}
    for key in required_keys:
        status[key] = get_secret(key) is not None
    return status


def get_api_keys() -> dict[str, Optional[str]]:
    """
    Get all API keys from secrets/environment.
    
    Returns:
        Dictionary with API key names and values
    """
    return {
        "FRED_API_KEY": get_secret("FRED_API_KEY"),
        "SEC_API_KEY": get_secret("SEC_API_KEY"),
    }


__all__ = [
    "get_secret",
    "get_secret_required",
    "validate_secrets",
    "get_api_keys",
]

