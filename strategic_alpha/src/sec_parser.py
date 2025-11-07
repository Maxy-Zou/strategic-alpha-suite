"""
SEC EDGAR 10-K parser for extracting risk factors.

This module fetches 10-K filings from SEC EDGAR and extracts Item 1A (Risk Factors).
Falls back to sample data when API is unavailable.
"""

import re
from pathlib import Path
from typing import Optional
import requests
from bs4 import BeautifulSoup
from rich.console import Console

console = Console()


def fetch_10k_filing(ticker: str, user_agent: str = "Strategic Alpha Suite admin@example.com") -> Optional[str]:
    """
    Fetch the most recent 10-K filing for a ticker from SEC EDGAR.

    Args:
        ticker: Stock ticker symbol (e.g., 'NVDA')
        user_agent: User agent string (required by SEC)

    Returns:
        HTML content of the 10-K filing, or None if not found
    """
    try:
        # SEC EDGAR API endpoint
        # First, get the CIK (Central Index Key) for the ticker
        cik = get_cik_for_ticker(ticker, user_agent)
        if not cik:
            console.print(f"[yellow]Could not find CIK for ticker {ticker}[/yellow]")
            return None

        # Fetch recent filings
        filings_url = f"https://data.sec.gov/submissions/CIK{cik:010d}.json"
        headers = {"User-Agent": user_agent}

        response = requests.get(filings_url, headers=headers, timeout=10)
        response.raise_for_status()

        filings_data = response.json()

        # Find the most recent 10-K filing
        recent_filings = filings_data.get("filings", {}).get("recent", {})
        forms = recent_filings.get("form", [])
        accession_numbers = recent_filings.get("accessionNumber", [])

        for i, form in enumerate(forms):
            if form == "10-K":
                accession = accession_numbers[i].replace("-", "")
                filing_url = f"https://www.sec.gov/cgi-bin/viewer?action=view&cik={cik}&accession_number={accession_numbers[i]}&xbrl_type=v"

                # Fetch the actual filing
                filing_response = requests.get(filing_url, headers=headers, timeout=30)
                filing_response.raise_for_status()

                console.print(f"[green]✓[/green] Fetched 10-K filing for {ticker}")
                return filing_response.text

        console.print(f"[yellow]No 10-K filings found for {ticker}[/yellow]")
        return None

    except requests.RequestException as e:
        console.print(f"[yellow]Warning: Failed to fetch 10-K from SEC: {e}[/yellow]")
        return None
    except Exception as e:
        console.print(f"[yellow]Unexpected error fetching 10-K: {e}[/yellow]")
        return None


def get_cik_for_ticker(ticker: str, user_agent: str) -> Optional[int]:
    """
    Get the CIK (Central Index Key) for a given ticker symbol.

    Args:
        ticker: Stock ticker symbol
        user_agent: User agent string

    Returns:
        CIK as integer, or None if not found
    """
    try:
        # Use SEC's company tickers JSON
        tickers_url = "https://www.sec.gov/files/company_tickers.json"
        headers = {"User-Agent": user_agent}

        response = requests.get(tickers_url, headers=headers, timeout=10)
        response.raise_for_status()

        tickers_data = response.json()

        # Search for the ticker
        ticker_upper = ticker.upper()
        for entry in tickers_data.values():
            if entry.get("ticker") == ticker_upper:
                return entry.get("cik_str")

        return None

    except Exception as e:
        console.print(f"[yellow]Failed to fetch CIK: {e}[/yellow]")
        return None


def extract_risk_factors(filing_html: str) -> str:
    """
    Extract Item 1A (Risk Factors) from a 10-K filing.

    Args:
        filing_html: HTML content of the 10-K filing

    Returns:
        Extracted risk factors text
    """
    try:
        soup = BeautifulSoup(filing_html, 'html.parser')

        # Get all text
        full_text = soup.get_text()

        # Try to find Item 1A - Risk Factors
        # Common patterns in 10-K filings
        patterns = [
            r'ITEM\s*1A[\.\s]*RISK\s*FACTORS(.*?)ITEM\s*1B',
            r'Item\s*1A[\.\s]*Risk\s*Factors(.*?)Item\s*1B',
            r'Item\s*1A\s*\.\s*Risk\s*Factors(.*?)Item\s*1B',
        ]

        for pattern in patterns:
            match = re.search(pattern, full_text, re.IGNORECASE | re.DOTALL)
            if match:
                risk_text = match.group(1)
                # Clean up the text
                risk_text = clean_risk_text(risk_text)
                console.print(f"[green]✓[/green] Extracted {len(risk_text)} characters of risk factors")
                return risk_text

        console.print("[yellow]Could not locate Risk Factors section in filing[/yellow]")
        return ""

    except Exception as e:
        console.print(f"[yellow]Error extracting risk factors: {e}[/yellow]")
        return ""


def clean_risk_text(text: str) -> str:
    """
    Clean extracted risk text by removing extra whitespace and formatting.

    Args:
        text: Raw extracted text

    Returns:
        Cleaned text
    """
    # Remove multiple spaces
    text = re.sub(r'\s+', ' ', text)

    # Remove page numbers and headers
    text = re.sub(r'\d+\s*Table of Contents', '', text, flags=re.IGNORECASE)

    # Trim
    text = text.strip()

    return text


def load_fallback_risk_factors(data_dir: Path) -> str:
    """
    Load sample risk factors from local file.

    Args:
        data_dir: Path to data directory

    Returns:
        Sample risk factors text
    """
    sample_file = data_dir / "financials" / "sample_10k_risk.txt"

    try:
        if sample_file.exists():
            return sample_file.read_text()
        else:
            console.print(f"[yellow]Sample risk factors file not found: {sample_file}[/yellow]")
            return generate_generic_risk_factors()
    except Exception as e:
        console.print(f"[yellow]Error loading fallback data: {e}[/yellow]")
        return generate_generic_risk_factors()


def generate_generic_risk_factors() -> str:
    """Generate generic risk factors as a last resort fallback."""
    return """
    Risk Factors (Generic Sample):

    Our business is subject to numerous risks, including:

    - Market Competition: We operate in highly competitive markets and may lose market share.
    - Supply Chain Risks: Disruptions to our supply chain could impact our ability to deliver products.
    - Regulatory Risks: Changes in regulations could affect our operations and profitability.
    - Technology Risks: Rapid technological change could make our products obsolete.
    - Economic Risks: Economic downturns could reduce demand for our products.
    - Geopolitical Risks: International tensions could affect our global operations.

    (Note: This is generic fallback data. Configure SEC_API_KEY for real 10-K data.)
    """


def get_risk_factors(ticker: str, data_dir: Path, sec_api_key: Optional[str] = None) -> str:
    """
    Get risk factors for a company, fetching from SEC EDGAR or using fallback.

    Args:
        ticker: Stock ticker symbol
        data_dir: Path to data directory for fallback
        sec_api_key: SEC API key (not required for direct EDGAR access)

    Returns:
        Risk factors text
    """
    console.print(f"\n[bold]Fetching Risk Factors for {ticker}...[/bold]")

    # Try to fetch from SEC EDGAR
    filing_html = fetch_10k_filing(ticker)

    if filing_html:
        risk_factors = extract_risk_factors(filing_html)
        if risk_factors and len(risk_factors) > 100:  # Ensure we got substantial content
            return risk_factors

    # Fallback to sample data
    console.print("[yellow]→ Using fallback risk factors data[/yellow]")
    return load_fallback_risk_factors(data_dir)


def analyze_risk_severity(risk_text: str) -> dict:
    """
    Analyze risk factors and categorize by type and severity.

    This is a simple keyword-based analysis. For production, use an LLM
    or fine-tuned ML model.

    Args:
        risk_text: Risk factors text

    Returns:
        Dictionary with risk categories and severity scores
    """
    risk_categories = {
        'supply_chain': {
            'keywords': ['supply chain', 'supplier', 'manufacturing', 'shortage', 'foundry', 'tsmc'],
            'score': 0,
            'mentions': 0
        },
        'geopolitical': {
            'keywords': ['geopolitical', 'china', 'taiwan', 'trade', 'export', 'sanctions'],
            'score': 0,
            'mentions': 0
        },
        'competition': {
            'keywords': ['competitive', 'competition', 'market share', 'competitors'],
            'score': 0,
            'mentions': 0
        },
        'regulatory': {
            'keywords': ['regulatory', 'regulation', 'compliance', 'legal'],
            'score': 0,
            'mentions': 0
        },
        'technology': {
            'keywords': ['technology', 'innovation', 'obsolete', 'advancement'],
            'score': 0,
            'mentions': 0
        },
        'demand': {
            'keywords': ['demand', 'customer', 'market', 'cyclical'],
            'score': 0,
            'mentions': 0
        }
    }

    risk_text_lower = risk_text.lower()

    for category, info in risk_categories.items():
        for keyword in info['keywords']:
            count = risk_text_lower.count(keyword)
            info['mentions'] += count

        # Score based on mentions (1-10 scale)
        if info['mentions'] == 0:
            info['score'] = 0
        elif info['mentions'] <= 2:
            info['score'] = 3
        elif info['mentions'] <= 5:
            info['score'] = 5
        elif info['mentions'] <= 10:
            info['score'] = 7
        else:
            info['score'] = 9

    return risk_categories


def summarize_risks(risk_categories: dict) -> str:
    """
    Generate a human-readable summary of risk analysis.

    Args:
        risk_categories: Dictionary from analyze_risk_severity()

    Returns:
        Formatted summary string
    """
    summary_lines = []
    summary_lines.append("\n[bold]Risk Factor Analysis:[/bold]")

    # Sort by score (highest first)
    sorted_risks = sorted(risk_categories.items(), key=lambda x: x[1]['score'], reverse=True)

    for risk_name, info in sorted_risks:
        if info['score'] > 0:
            severity = "Low" if info['score'] <= 3 else "Medium" if info['score'] <= 6 else "High"
            color = "green" if severity == "Low" else "yellow" if severity == "Medium" else "red"

            risk_display = risk_name.replace('_', ' ').title()
            summary_lines.append(
                f"  [{color}]{risk_display}[/{color}]: "
                f"{severity} ({info['score']}/10) - {info['mentions']} mentions"
            )

    return "\n".join(summary_lines)


if __name__ == "__main__":
    # Demo usage
    from pathlib import Path

    demo_ticker = "NVDA"
    demo_data_dir = Path(__file__).parent.parent / "data"

    risk_text = get_risk_factors(demo_ticker, demo_data_dir)
    print(f"\nRisk Factors (first 500 chars):\n{risk_text[:500]}...\n")

    risk_analysis = analyze_risk_severity(risk_text)
    summary = summarize_risks(risk_analysis)
    console.print(summary)
