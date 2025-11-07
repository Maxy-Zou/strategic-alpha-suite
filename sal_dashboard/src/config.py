"""
Configuration utilities for the Streamlit dashboard.
"""

from __future__ import annotations

import importlib.util
import os
import sys
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any, Dict, Iterable, Optional

from dotenv import load_dotenv

load_dotenv()

ROOT_DIR = Path(__file__).resolve().parents[1]
BACKEND_DIR = ROOT_DIR.parent / "strategic_alpha"
BACKEND_SRC_DIR = BACKEND_DIR / "src"

if not BACKEND_SRC_DIR.exists():
    raise RuntimeError(
        "Expected backend repository at '../strategic_alpha/src'. "
        "Please ensure Prompt A backend is available."
    )


def _ensure_backend_package() -> str:
    """Create a synthetic package so backend relative imports resolve."""
    package_name = "strategic_alpha"
    if package_name not in sys.modules:
        package = ModuleType(package_name)
        package.__path__ = [str(BACKEND_SRC_DIR)]  # type: ignore[attr-defined]
        sys.modules[package_name] = package
    return package_name


def _load_backend_module(module_name: str):
    """Dynamically load a backend module from strategic_alpha/src."""
    package_prefix = _ensure_backend_package()
    module_key = f"{package_prefix}.{module_name}"
    if module_key in sys.modules:
        return sys.modules[module_key]

    module_path = BACKEND_SRC_DIR / f"{module_name}.py"
    if not module_path.exists():
        raise ImportError(f"Module {module_name} not found in backend repo.")

    spec = importlib.util.spec_from_file_location(module_key, module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to load module {module_name}")

    module = importlib.util.module_from_spec(spec)
    # Set __package__ so relative imports work
    module.__package__ = package_prefix
    sys.modules[module_key] = module
    spec.loader.exec_module(module)
    return module


backend_config = _load_backend_module("config")
BackendSettings = backend_config.Settings


def _split_env_list(value: Optional[str], default: Iterable[str]) -> list[str]:
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


def _build_settings(overrides: Optional[Dict[str, Any]] = None) -> Any:
    """
    Return a backend Settings instance with directories pointed to this project.
    """

    overrides = overrides or {}
    defaults: Dict[str, Any] = {
        "fred_api_key": os.getenv("FRED_API_KEY"),
        "sec_api_key": os.getenv("SEC_API_KEY"),
        "shock_pct": float(os.getenv("SHOCK_PCT", "-0.10")),
        "risk_peer_tickers": _split_env_list(
            os.getenv("RISK_PEER_TICKERS"),
            ["AMD", "AVGO", "TSM", "ASML", "INTC"],
        ),
        "supply_shock_tickers": _split_env_list(
            os.getenv("SUPPLY_SHOCK_TICKERS"), ["TSM", "ASML"]
        ),
        "data_dir": ROOT_DIR / "data",
        "artifacts_dir": ROOT_DIR / "artifacts",
        "reports_dir": ROOT_DIR / "reports",
    }

    # Ensure directories exist to avoid backend errors.
    for key in ("data_dir", "artifacts_dir", "reports_dir"):
        Path(defaults[key]).mkdir(parents=True, exist_ok=True)

    defaults.update(overrides)
    return BackendSettings(**defaults)


@lru_cache(maxsize=1)
def get_settings() -> Any:
    """Return cached settings without overrides."""
    return _build_settings()


def clone_settings(base_settings: Any, **updates: Any) -> Any:
    """Create a modified copy of backend settings."""
    payload: Dict[str, Any]
    if hasattr(base_settings, "model_dump"):
        payload = dict(base_settings.model_dump())
    elif hasattr(base_settings, "dict"):
        payload = dict(base_settings.dict())  # type: ignore[attr-defined]
    else:  # pragma: no cover
        payload = base_settings.__dict__.copy()
    payload.update(updates)
    return BackendSettings(**payload)


def get_backend_module(module_name: str):
    """Expose backend module loader to downstream modules."""
    return _load_backend_module(module_name)


__all__ = ["get_settings", "clone_settings", "get_backend_module", "ROOT_DIR"]
