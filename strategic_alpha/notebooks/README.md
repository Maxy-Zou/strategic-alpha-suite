# Strategic Alpha Suite - Analysis Notebooks

This directory contains Jupyter notebooks demonstrating the Strategic Alpha Suite's analytical capabilities.

## Available Notebooks

### 1. NVDA Deep Dive Analysis (`nvda_deep_dive.ipynb`)

Comprehensive investment analysis of NVIDIA Corporation (NVDA) showcasing all Strategic Alpha Suite features:

**Sections:**
- Executive Summary with valuation snapshot
- DCF Analysis with sensitivity tables
- Risk Assessment (VaR, stress tests, volatility analysis)
- Supply Chain Network Analysis
- SEC 10-K Risk Factor extraction and scoring
- Macroeconomic context
- Investment Thesis & Price Target

**Use Cases:**
- Portfolio-ready analysis for sharing with recruiters
- Template for analyzing other semiconductor companies
- Demonstration of quantitative finance skills
- Educational resource for DCF/risk modeling

## Getting Started

### Prerequisites

```bash
# Ensure you're in the strategic_alpha directory
cd strategic_alpha

# Activate virtual environment
source venv/bin/activate  # Unix/macOS
# or
.\venv\Scripts\activate  # Windows

# Install Jupyter if not already installed
pip install jupyter notebook ipykernel
```

### Running the Notebooks

1. **Start Jupyter Notebook:**
   ```bash
   jupyter notebook notebooks/nvda_deep_dive.ipynb
   ```

2. **Run all cells:**
   - In Jupyter: `Cell > Run All`
   - Or run cells sequentially with `Shift+Enter`

3. **Expected runtime:** 2-3 minutes for full analysis

### Configuration

The notebooks use your Strategic Alpha Suite configuration:

- **API Keys**: Set in `.env` file (see `.env.example`)
  - `FRED_API_KEY` - For macroeconomic data (optional)
  - `SEC_API_KEY` - For SEC EDGAR data (optional)

- **Settings**: Configured via `src/config.py`
  - Peer tickers, risk parameters, data directories

### Exporting Results

#### Export to PDF

```bash
# Option 1: Direct PDF export (requires LaTeX)
jupyter nbconvert --to pdf notebooks/nvda_deep_dive.ipynb

# Option 2: HTML first (easier, no dependencies)
jupyter nbconvert --to html notebooks/nvda_deep_dive.ipynb
# Then print to PDF from browser

# Option 3: Via Jupyter interface
# File > Download as > PDF via LaTeX
```

#### Export to HTML (for sharing)

```bash
jupyter nbconvert --to html notebooks/nvda_deep_dive.ipynb --output-dir=./reports
```

#### Export charts as images

Charts are displayed inline and can be exported by:
- Right-clicking and saving images
- Programmatically saving with `plt.savefig()`

## Customization

### Analyze a Different Company

To analyze another company, modify the notebook:

```python
# Change this line
TICKER = 'AMD'  # or 'INTC', 'TSM', etc.

# Adjust peer companies
PEER_TICKERS = ['NVDA', 'INTC', 'AVGO', 'TSM', 'ASML']
```

### Adjust Analysis Parameters

```python
# Change date range
start_date = '2022-01-01'
end_date = '2024-12-31'

# Modify DCF assumptions
# (Will be configurable via dashboard in Week 2)
```

### Add Custom Sections

The notebook is structured modularly - you can add sections like:
- Competitor comparison analysis
- Historical valuation multiples
- Technical analysis
- Earnings call sentiment analysis

## Troubleshooting

### Common Issues

**1. Module not found errors:**
```bash
# Ensure you're in the right directory
cd strategic_alpha

# Reinstall in development mode
pip install -e .
```

**2. API key errors:**
```bash
# Copy example env file
cp .env.example .env

# Edit .env with your API keys
# Note: Analysis runs without API keys, but some features are limited
```

**3. Data fetching timeouts:**
- Increase timeout in `src/config.py`
- Check internet connection
- Some data sources may be temporarily unavailable

**4. Memory errors on large datasets:**
- Reduce date range
- Sample data instead of full historical dataset
- Close other applications

### Getting Help

- Check [main README](../README.md) for setup instructions
- Review [TESTING.md](../TESTING.md) for debugging tips
- Open an issue on GitHub with error messages

## Portfolio Use

### For Job Applications

This notebook demonstrates:
- ✅ Financial modeling (DCF, VaR)
- ✅ Data analysis and visualization
- ✅ Risk management frameworks
- ✅ Software engineering (modular code, testing)
- ✅ Domain knowledge (semiconductors, supply chain)

**How to share:**
1. Export to PDF (clean, professional)
2. Upload to GitHub (code visibility)
3. Host on nbviewer (interactive preview)
4. Reference in resume/cover letter

### Sample Resume Bullet Points

> - Built Strategic Alpha Suite: Python-based financial analysis platform for semiconductor valuation
> - Implemented DCF model with Monte Carlo simulation (10,000 iterations) and sensitivity analysis
> - Developed automated SEC 10-K risk factor extraction with NLP-based severity scoring
> - Created Value at Risk (VaR) framework for portfolio risk management
> - Integrated supply chain network analysis using graph theory and centrality metrics

### Interview Talking Points

Be prepared to discuss:
- **Technical**: DCF methodology, WACC calculation, VaR vs CVaR
- **Implementation**: Python data pipeline, API integration, error handling
- **Insights**: Key findings from your NVDA analysis
- **Extensions**: How you'd improve the model (ML, real-time data, etc.)

## Next Steps

See the [Phase 1 roadmap](../README.md#phase-1-portfolio-launch) for:
- Week 2: Interactive DCF parameters in dashboard
- Week 3-4: ML-enhanced risk scoring
- Week 5-6: Real-time data pipelines
- Week 7-8: Monetization features

---

**Generated as part of Strategic Alpha Suite v0.1.0**
**For questions or contributions, see [CONTRIBUTING.md](../CONTRIBUTING.md)**
