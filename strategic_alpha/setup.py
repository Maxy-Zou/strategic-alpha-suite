"""Setup script for Strategic Alpha backend package."""

from setuptools import setup, find_packages
from pathlib import Path

# Read requirements
requirements_path = Path(__file__).parent / "requirements.txt"
with open(requirements_path) as f:
    requirements = [line.strip() for line in f if line.strip() and not line.startswith("#")]

# Read README
readme_path = Path(__file__).parent.parent / "README.md"
long_description = ""
if readme_path.exists():
    with open(readme_path, encoding="utf-8") as f:
        long_description = f.read()

setup(
    name="strategic-alpha",
    version="0.1.0",
    description="Macro, supply-chain, valuation, and risk analytics for semiconductor companies",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Max Zou",
    author_email="max@example.com",
    url="https://github.com/Maxy-Zou/strategic-alpha-suite",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.10",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0",
            "pytest-cov>=4.0",
            "pytest-mock>=3.10",
            "black>=24.0",
            "ruff>=0.3",
            "mypy>=1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "sal=strategic_alpha.analyze_company:app",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Financial and Insurance Industry",
        "Topic :: Office/Business :: Financial :: Investment",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="finance investment semiconductor analysis dcf valuation risk",
)
