"""
Application configuration using Pydantic settings.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic import Field

try:  # Pydantic v2
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:  # Pydantic v1 fallback
    from pydantic import BaseSettings  # type: ignore

    SettingsConfigDict = None  # type: ignore


class _SettingsBase(BaseSettings):
    fred_api_key: str | None = Field(default=None, validation_alias="FRED_API_KEY")
    sec_api_key: str | None = Field(default=None, validation_alias="SEC_API_KEY")
    shock_pct: float = Field(default=-0.10, validation_alias="SHOCK_PCT")
    risk_peer_tickers: List[str] = Field(
        default_factory=lambda: ["AMD", "AVGO", "TSM", "ASML", "INTC"],
        validation_alias="RISK_PEER_TICKERS",
    )
    supply_shock_tickers: List[str] = Field(
        default_factory=lambda: ["TSM", "ASML"],
        validation_alias="SUPPLY_SHOCK_TICKERS",
    )

    data_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "data"
    )
    artifacts_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "artifacts"
    )
    reports_dir: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[1] / "reports"
    )


if SettingsConfigDict is not None:

    class Settings(_SettingsBase):
        """Central configuration loaded from environment variables or .env file."""

        model_config = SettingsConfigDict(
            env_file=".env",
            env_file_encoding="utf-8",
            case_sensitive=False,
            extra="allow",
        )

else:

    class Settings(_SettingsBase):
        """Central configuration loaded from environment variables or .env file."""

        class Config:
            env_file = ".env"
            env_file_encoding = "utf-8"
            case_sensitive = False
            extra = "allow"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""
    settings = Settings()
    settings.artifacts_dir.mkdir(parents=True, exist_ok=True)
    settings.reports_dir.mkdir(parents=True, exist_ok=True)
    return settings


__all__ = ["Settings", "get_settings"]
