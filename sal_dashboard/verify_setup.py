#!/usr/bin/env python3
"""
Verify that the dashboard setup is correct and all dependencies are available.
"""

import sys
from pathlib import Path

# Add sal_dashboard to path (same as streamlit_app.py does)
sal_dashboard_dir = Path(__file__).resolve().parent
if str(sal_dashboard_dir) not in sys.path:
    sys.path.insert(0, str(sal_dashboard_dir))

def check_imports():
    """Check that all required imports work."""
    print("Checking imports...\n")
    errors = []

    # Standard library
    try:
        import re, time, traceback
        from datetime import date, datetime, timedelta
        from typing import Any, Dict, Iterable
        print("✓ Standard library imports")
    except Exception as e:
        errors.append(f"Standard library: {e}")
        print(f"✗ Standard library: {e}")

    # Third-party
    try:
        import pandas as pd
        import streamlit as st
        import yfinance as yf
        import numpy as np
        import matplotlib.pyplot as plt
        import plotly.graph_objects as go
        print("✓ Third-party imports (pandas, streamlit, yfinance, numpy, matplotlib, plotly)")
    except Exception as e:
        errors.append(f"Third-party: {e}")
        print(f"✗ Third-party: {e}")

    # App components
    try:
        from app.components.charts import dcf_heatmap, macro_chart, price_chart, risk_histogram
        from app.components.kpi_cards import render_kpi_cards
        from app.components.tables import format_chokepoints, format_comps
        print("✓ App components imports")
    except Exception as e:
        errors.append(f"App components: {e}")
        print(f"✗ App components: {e}")

    # Src modules
    try:
        from src import macro, risk, supply, valuation
        from src.config import ROOT_DIR, get_settings
        from src.database import get_db
        from src.health import check_health, get_metrics
        from src.logging_config import get_logger, setup_logging
        from src.rate_limiter import get_rate_limiter
        print("✓ Src modules imports")
    except Exception as e:
        errors.append(f"Src modules: {e}")
        print(f"✗ Src modules: {e}")

    return errors

def check_config():
    """Check configuration."""
    print("\nChecking configuration...\n")

    env_file = Path(".env")
    if env_file.exists():
        print(f"✓ .env file exists")

        # Try to load settings
        try:
            from src.config import get_settings
            settings = get_settings()
            print(f"✓ Settings loaded successfully")
            print(f"  - Data dir: {settings.data_dir}")
            print(f"  - Artifacts dir: {settings.artifacts_dir}")
            print(f"  - Reports dir: {settings.reports_dir}")

            if settings.fred_api_key:
                print(f"  - FRED API key: configured")
            else:
                print(f"  - FRED API key: not set (will use sample data)")

        except Exception as e:
            print(f"✗ Error loading settings: {e}")
    else:
        print(f"⚠  .env file not found (optional - app will use defaults)")

def check_directories():
    """Check required directories."""
    print("\nChecking directories...\n")

    dirs_to_check = [
        ("app/components", "App components"),
        ("src", "Source modules"),
        ("data", "Data directory"),
        ("logs", "Logs directory"),
    ]

    for dir_path, description in dirs_to_check:
        path = Path(dir_path)
        if path.exists():
            print(f"✓ {description}: {dir_path}")
        else:
            print(f"⚠  {description}: {dir_path} (will be created on first run)")

def main():
    print("=" * 70)
    print("Strategic Alpha Dashboard - Setup Verification")
    print("=" * 70)
    print()

    # Check imports
    errors = check_imports()

    # Check config
    check_config()

    # Check directories
    check_directories()

    # Summary
    print("\n" + "=" * 70)
    if errors:
        print("❌ SETUP INCOMPLETE - Please fix the following errors:")
        for error in errors:
            print(f"   • {error}")
        print("\nRun: pip install -r requirements.txt")
        return 1
    else:
        print("✅ SETUP VERIFIED - Dashboard is ready to run!")
        print("\nTo start the dashboard:")
        print("   streamlit run app/streamlit_app.py")
        return 0

if __name__ == "__main__":
    sys.exit(main())
