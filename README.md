# 🚀 Strategic Alpha Suite

<div align="center">

[![CI](https://github.com/Maxy-Zou/strategic-alpha-suite/actions/workflows/ci.yml/badge.svg)](https://github.com/Maxy-Zou/strategic-alpha-suite/actions)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

**Institutional-grade investment research platform for semiconductor companies**

🚧 [Live Demo](https://strategic-alpha.streamlit.app) (deploying soon) • [Documentation](#documentation) • [Quick Start](#quickstart)

</div>

---

## 📋 Overview

Strategic Alpha Suite is a comprehensive investment research toolkit that combines quantitative analysis, supply chain intelligence, and AI-powered insights to evaluate semiconductor companies. Built with production-ready infrastructure including comprehensive logging, rate limiting, database tracking, and Docker deployment.

### 🎯 Key Differentiators

- **SEC EDGAR Integration**: Automatic 10-K risk factor extraction and AI-powered severity scoring
- **Supply Chain Network Analysis**: NetworkX-based chokepoint identification for geopolitical risk assessment
- **DCF Valuation with Sensitivity Analysis**: Institutional-grade models with WACC vs growth heatmaps
- **Offline-First Architecture**: Works without API keys using deterministic fallbacks
- **Production-Ready**: Logging, monitoring, health checks, rate limiting, and comprehensive test coverage

### 💼 Skills Demonstrated

This project showcases professional software engineering practices valued by employers:

| Category | Skills |
|----------|---------|
| **Backend Development** | Python 3.12+, Typer CLI, Pydantic validation, async operations |
| **Frontend/UI** | Streamlit dashboards, responsive design, interactive visualizations |
| **Data Engineering** | ETL pipelines, data validation, API integration (FRED, SEC EDGAR, yfinance) |
| **Financial Analysis** | DCF modeling, VaR calculations, supply chain network analysis, risk assessment |
| **Database** | SQLite, ORM patterns, migration strategies, query optimization |
| **Testing** | pytest (80%+ coverage), fixtures, mocking, integration tests, CI/CD |
| **DevOps** | Docker, docker-compose, multi-stage builds, health checks, logging |
| **Code Quality** | Black, ruff, mypy, pre-commit hooks, type hints, documentation |
| **Architecture** | Modular design, separation of concerns, offline-first, graceful degradation |
| **Production Readiness** | Rate limiting, structured logging, error handling, monitoring, secrets management |

### 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   Strategic Alpha Suite                      │
├─────────────────────────┬───────────────────────────────────┤
│  Backend (CLI)          │  Frontend (Dashboard)             │
│  strategic_alpha/       │  sal_dashboard/                   │
│                         │                                   │
│  • Macro Analysis       │  • 7 Interactive Tabs             │
│  • Supply Mapping       │  • Real-time Charts               │
│  • DCF Valuation        │  • Admin Monitoring               │
│  • Risk Metrics (VaR)   │  • Report Generation              │
│  • SEC Parser           │  • Historical Tracking            │
│                         │                                   │
│  Data Sources:          │  Infrastructure:                  │
│  ├─ yfinance            │  ├─ SQLite Database               │
│  ├─ FRED API            │  ├─ Rate Limiter                  │
│  ├─ SEC EDGAR           │  ├─ Health Checks                 │
│  └─ Sample CSVs         │  ├─ Structured Logging            │
│     (fallback)          │  └─ Docker Ready                  │
└─────────────────────────┴───────────────────────────────────┘
```

---

## ✨ Features

### 📊 Multi-Dimensional Analysis

| Module | Features |
|--------|----------|
| **Macro Context** | • CPI, unemployment, Fed funds rate, industrial production<br/>• Z-score normalization & trend analysis<br/>• FRED API with CSV fallback |
| **Supply Chain** | • NetworkX graph visualization<br/>• Betweenness centrality for chokepoints<br/>• Geographic concentration risk scoring<br/>• 20+ semiconductor relationships mapped |
| **Valuation** | • DCF with 5-year projections<br/>• Terminal value using Gordon Growth<br/>• WACC vs terminal growth sensitivity heatmaps<br/>• Peer comparables (P/E, EV/EBITDA, P/S)<br/>• Percentile positioning vs competitors |
| **Risk Analytics** | • Historical VaR (95%, 99%)<br/>• Variance-Covariance VaR<br/>• Configurable stress testing (Taiwan shock scenario)<br/>• Return distribution histograms |
| **SEC Filings** | • 10-K Item 1A extraction<br/>• Automatic risk categorization (6 types)<br/>• Severity scoring (1-10 scale)<br/>• Keyword-based analysis |

### 🖥️ Interactive Dashboard

<div align="center">

📸 *Dashboard screenshots coming soon - see [Quick Start](#quickstart) to run locally*

</div>

**7 Comprehensive Tabs:**
1. **Overview**: KPI cards, 12-month price chart, key metrics
2. **Macro Context**: Economic indicators with AI-generated commentary
3. **Supply Map**: Interactive network visualization, chokepoint analysis
4. **Valuation**: Editable DCF inputs, sensitivity heatmap, peer comparison table
5. **Risk**: VaR metrics, stress test results, return histogram
6. **Report**: Generate & download professional investment memos
7. **Admin**: System health, API metrics, valuation history, error logs

### 🏭 Production Features

- ✅ **Rate Limiting**: 60 calls/min, 1000 calls/hour with exponential backoff
- ✅ **Comprehensive Logging**: Structured logs with rotation (10MB, 5 backups)
- ✅ **Database Tracking**: SQLite for valuations, API calls, interactions, errors
- ✅ **Health Monitoring**: Disk space, database connectivity, directory validation
- ✅ **Error Handling**: User-friendly messages with graceful degradation
- ✅ **Secrets Management**: Streamlit secrets + .env fallback
- ✅ **Docker Deployment**: Multi-stage builds, health checks, volume mounts
- ✅ **Test Coverage**: 80%+ with pytest, comprehensive fixtures
- ✅ **CI/CD**: GitHub Actions for automated testing
- ✅ **Pre-commit Hooks**: black, ruff, mypy, isort, flake8

---

## 🚀 Quickstart

### Option 1: Docker (Recommended)

```bash
git clone https://github.com/Maxy-Zou/strategic-alpha-suite.git
cd strategic-alpha-suite/sal_dashboard

# Start the dashboard
docker-compose up

# Access at http://localhost:8501
```

### Option 2: Local Setup

```bash
# Clone repository
git clone https://github.com/Maxy-Zou/strategic-alpha-suite.git
cd strategic-alpha-suite

# Set up environments
make setup

# Install pre-commit hooks
make install-hooks

# Run backend CLI analysis
cd strategic_alpha
./venv/bin/python -m src.analyze_company full --ticker NVDA

# Start dashboard
cd ../sal_dashboard
./venv/bin/streamlit run app/streamlit_app.py
```

### Option 3: Quick Demo (No Setup)

```bash
# Run CLI demo (works offline with sample data)
./scripts/sal run --ticker NVDA

# Launch dashboard (requires streamlit installed)
make dashboard
```

---

## 📖 Documentation

- **[TESTING.md](TESTING.md)**: Testing guide, coverage goals, fixtures
- **[DEPLOYMENT.md](sal_dashboard/DEPLOYMENT.md)**: Docker, Streamlit Cloud, production setup
- **[CONTRIBUTING.md](CONTRIBUTING.md)**: Development guidelines
- **[SECURITY.md](SECURITY.md)**: Security policy

### 📚 Usage Examples

```python
# Backend: Run DCF valuation
from strategic_alpha.valuation import run_dcf_analysis

result = run_dcf_analysis(
    ticker='NVDA',
    start_date='2023-01-01',
    end_date='2024-01-01',
    peers=['AMD', 'INTC'],
    data_dir=Path('data'),
    artifacts_dir=Path('artifacts')
)

print(f"DCF Value: ${result['dcf_value']/1e9:.2f}B")
print(f"Upside: {result['upside']:.1%}")
```

```bash
# CLI: Run full analysis with all modules
python -m src.analyze_company full --ticker NVDA

# CLI: Run specific modules
python -m src.analyze_company macro
python -m src.analyze_company supply --ticker NVDA
python -m src.analyze_company valuation --ticker NVDA --start 2023-01-01
```

---

## 🛠️ Technology Stack

### Backend
- **Python 3.12**: Core language
- **Typer**: CLI framework
- **yfinance**: Stock data & fundamentals
- **fredapi**: Federal Reserve economic data
- **pandas/numpy**: Data manipulation
- **networkx**: Graph analysis for supply chains
- **matplotlib/plotly**: Visualization
- **scipy**: Statistical calculations
- **pydantic**: Settings & validation
- **requests/BeautifulSoup**: SEC EDGAR scraping

### Frontend
- **Streamlit**: Interactive web application
- **plotly**: Dynamic visualizations
- **SQLite**: Data persistence
- **python-dotenv**: Configuration management

### Infrastructure
- **Docker**: Containerization
- **GitHub Actions**: CI/CD
- **pytest**: Testing framework (80%+ coverage)
- **black/ruff/mypy**: Code quality
- **pre-commit**: Git hooks

---

## 🎯 Use Cases

### 1. Investment Research
> "Evaluate NVIDIA's AI boom: Is the stock overvalued given Taiwan concentration risk?"

**Workflow:**
1. Run macro analysis → Fed policy supportive?
2. Check supply chain → TSMC dependency quantified
3. DCF valuation → Fair value vs current price
4. Risk metrics → 99% VaR during volatility
5. SEC filing → Identify new regulatory risks
6. Generate investment memo → Professional 2-page thesis

### 2. Portfolio Management
> "Screen 50 semiconductor stocks to find top 5 undervalued with low supply risk"

**Workflow:**
1. Batch analyze tickers
2. Filter by DCF upside >20%
3. Sort by supply chain chokepoint score
4. Review risk factors
5. Export to Excel for further review

### 3. Risk Assessment
> "What's our portfolio exposure to a Taiwan geopolitical event?"

**Workflow:**
1. Map supply chain for all holdings
2. Identify TSMC dependencies
3. Run stress test with -20% Taiwan shock
4. Calculate portfolio-level VaR
5. Generate risk report

---

## 📊 Sample Output

### CLI Output
```
Strategic Alpha Analysis: NVDA (2023-01-01 to 2024-01-01)

Macro Environment:
  CPI: 3.2% (normalized: 0.8)
  Unemployment: 3.7% (normalized: -0.3)
  Fed Funds Rate: 5.33% (normalized: 1.2)
  → Environment: MODERATELY HAWKISH

Supply Chain:
  Critical Dependencies: TSMC (betweenness: 0.85)
  Geographic Risk: Taiwan 75%, South Korea 15%
  Chokepoint Score: 8.5/10 (HIGH RISK)

Valuation:
  Current Price: $450.25
  DCF Fair Value: $387.50
  Upside/Downside: -14.0% (OVERVALUED)
  Peer Comparison: Trading at 95th percentile

Risk Metrics:
  VaR (95%): -$2.8B
  VaR (99%): -$4.2B
  Taiwan Shock Impact: -18% portfolio value

Investment Thesis: HOLD
While fundamentals remain strong, current valuation fully prices
in AI growth. Taiwan geopolitical risk creates -20% downside scenario.
Wait for pullback to $380-400 range.

Report saved to: reports/NVDA_2024-01-15.md
```

---

## 🔧 Configuration

### Environment Variables

Create `.env` file (optional - works without):

```bash
# Economic Data (optional - has CSV fallback)
FRED_API_KEY=your_fred_api_key_here

# SEC EDGAR Configuration (NO API KEY NEEDED!)
# SEC requires a User-Agent header with your name and email
# Format: "Your Name your.email@example.com"
# See: https://www.sec.gov/os/accessing-edgar-data
SEC_USER_NAME=Your Name
SEC_USER_EMAIL=your.email@example.com

# Analysis Parameters
SHOCK_PCT=-0.10                          # Default shock for stress tests
RISK_PEER_TICKERS=AMD,AVGO,TSM,ASML,INTC
SUPPLY_SHOCK_TICKERS=TSM,ASML
```

**Get API Keys (Free):**
- FRED: https://fred.stlouisfed.org/docs/api/api_key.html (optional but recommended)
- SEC EDGAR: No API key needed! Just provide your contact info per SEC guidelines

---

## 🧪 Testing

```bash
# Run all tests with coverage
make test

# Run backend tests only
make test-backend

# Run dashboard tests only
make test-dashboard

# Generate HTML coverage report
cd strategic_alpha && pytest tests/ --cov=src --cov-report=html
# Open htmlcov/index.html
```

**Test Coverage:**
- Backend: 85%+ coverage
- Dashboard: 80%+ coverage
- Critical paths (DCF, database, rate limiter): 90%+

---

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

**Development Workflow:**
```bash
# 1. Set up development environment
make setup
make install-hooks

# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Make changes and test
make test
make lint
make fmt

# 4. Pre-commit hooks run automatically on commit
git commit -m "feat: add my feature"

# 5. Push and create PR
git push origin feature/my-new-feature
```

---

## 📈 Roadmap

### Phase 2 (Completed ✅)
- [x] Production infrastructure (logging, rate limiting, health checks)
- [x] Docker deployment
- [x] Comprehensive test suite (80%+ coverage)
- [x] SEC EDGAR integration
- [x] Pre-commit hooks

### Phase 3 (In Progress)
- [ ] LLM-powered investment memo generation
- [ ] Earnings call sentiment analysis
- [ ] Real-time price updates via WebSocket
- [ ] Comparison/screening mode
- [ ] Jupyter notebook demos

### Phase 4 (Planned)
- [ ] User authentication & multi-user support
- [ ] PostgreSQL migration for better concurrency
- [ ] Redis caching layer
- [ ] Alert system (price, valuation, news)
- [ ] FastAPI endpoints for programmatic access
- [ ] Prometheus metrics & Grafana dashboards

See [detailed roadmap](docs/ROADMAP.md) for full plan.

---

## 📜 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- Built with [Streamlit](https://streamlit.io/) for the interactive dashboard
- Economic data from [FRED](https://fred.stlouisfed.org/)
- Financial data from [yfinance](https://github.com/ranaroussi/yfinance)
- SEC data from [EDGAR](https://www.sec.gov/edgar)
- Network analysis with [NetworkX](https://networkx.org/)

---

## 📞 Contact

**Max Zou**
[GitHub](https://github.com/Maxy-Zou) • [LinkedIn](https://linkedin.com/in/maxyzou) • [Email](mailto:maxzou0325@gmail.com)

---

<div align="center">

**⭐ Star this repo if you find it useful!**

[![GitHub stars](https://img.shields.io/github/stars/Maxy-Zou/strategic-alpha-suite?style=social)](https://github.com/Maxy-Zou/strategic-alpha-suite/stargazers)

</div>
