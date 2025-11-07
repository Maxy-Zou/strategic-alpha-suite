# Strategic Alpha Suite - Architecture

## System Overview

The Strategic Alpha Suite is a modular financial analysis platform consisting of two main components:

1. **Strategic Alpha Backend** (`strategic_alpha/`) - Core analytical engine
2. **SAL Dashboard** (`sal_dashboard/`) - Interactive web interface

```
┌─────────────────────────────────────────────────────────────────────┐
│                     Strategic Alpha Suite                            │
│                    (Semiconductor Analytics)                         │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────┐         ┌──────────────────────────────┐
│   Frontend Layer        │         │     Backend Engine           │
│   (sal_dashboard/)      │────────▶│   (strategic_alpha/)         │
│                         │         │                              │
│  ┌──────────────────┐  │         │  ┌────────────────────────┐ │
│  │ Streamlit App    │  │         │  │  Analysis Modules      │ │
│  │  streamlit_app.py│  │         │  │  ──────────────────    │ │
│  │                  │  │         │  │  • valuation_model.py  │ │
│  │  - KPI Cards     │  │         │  │  • risk_model.py       │ │
│  │  - Charts        │  │         │  │  • supply_mapping.py   │ │
│  │  - Tables        │  │         │  │  • sec_edgar.py        │ │
│  │  - Reports       │  │         │  │  • macro_dashboard.py  │ │
│  └──────────────────┘  │         │  └────────────────────────┘ │
│                         │         │                              │
│  ┌──────────────────┐  │         │  ┌────────────────────────┐ │
│  │ Infrastructure   │  │         │  │  Data Fetchers         │ │
│  │  ──────────────  │  │         │  │  ──────────────        │ │
│  │  • Database      │  │         │  │  • yfinance            │ │
│  │  • Logging       │  │         │  │  • FRED API            │ │
│  │  • Rate Limiter  │  │         │  │  • SEC EDGAR API       │ │
│  │  • Health Checks │  │         │  │  • pandas_datareader   │ │
│  └──────────────────┘  │         │  └────────────────────────┘ │
└─────────────────────────┘         └──────────────────────────────┘
          │                                      │
          │                                      │
          ▼                                      ▼
┌─────────────────────────┐         ┌──────────────────────────────┐
│   Data Layer            │         │   External APIs              │
│   ──────────            │         │   ─────────────              │
│  • SQLite Database      │         │  • Yahoo Finance (yfinance)  │
│  • File System Cache    │         │  • Federal Reserve (FRED)    │
│  • JSON Reports         │         │  • SEC EDGAR                 │
│  • CSV Exports          │         │  • Alpha Vantage (optional)  │
└─────────────────────────┘         └──────────────────────────────┘
```

## Component Architecture

### 1. Strategic Alpha Backend (`strategic_alpha/`)

**Purpose**: Core analytical engine for semiconductor company valuation and risk analysis

**Key Modules:**

```
strategic_alpha/
├── src/
│   ├── valuation_model.py     # DCF valuation with WACC
│   ├── risk_model.py           # VaR, stress testing, volatility
│   ├── supply_mapping.py       # Supply chain network analysis
│   ├── sec_edgar.py            # 10-K risk factor extraction
│   ├── macro_dashboard.py      # Macroeconomic indicators
│   └── config.py               # Configuration management
├── tests/                      # Comprehensive test suite (57 tests)
├── notebooks/                  # Analysis notebooks (NVDA deep dive)
└── artifacts/                  # Generated reports and charts
```

**Data Flow:**
```
User Input (ticker, dates, peers)
    ↓
Configuration Loading (config.py)
    ↓
Data Fetching (yfinance, FRED, SEC)
    ↓
Analysis Pipeline:
    • DCF Model → Fair value calculation
    • Risk Model → VaR, stress tests
    • Supply Chain → Network analysis
    • SEC Parser → Risk extraction
    • Macro → Economic context
    ↓
Results:
    • JSON reports
    • CSV data files
    • Visualizations
```

### 2. SAL Dashboard (`sal_dashboard/`)

**Purpose**: Interactive web interface for real-time analysis

**Architecture Pattern**: Streamlit App + Production Infrastructure

```
sal_dashboard/
├── app/
│   ├── streamlit_app.py        # Main application
│   └── components/
│       ├── charts.py           # Visualization components
│       ├── kpi_cards.py        # Metric displays
│       └── tables.py           # Data tables
├── src/
│   ├── database.py             # SQLite persistence
│   ├── logging_config.py       # Structured logging
│   ├── rate_limiter.py         # API rate limiting
│   ├── health.py               # Health monitoring
│   └── secrets_manager.py      # Secure config
├── .streamlit/
│   ├── config.toml             # UI configuration
│   └── secrets.toml.example    # Secrets template
└── tests/                      # Dashboard tests (51 tests)
```

**Request Flow:**
```
User Interaction (Browser)
    ↓
Streamlit App (streamlit_app.py)
    ↓
Session Management + Caching
    ↓
Rate Limited API Calls
    ↓
Strategic Alpha Backend (via imports)
    ↓
Database Logging (user interactions, API calls)
    ↓
Render Results (charts, tables, reports)
    ↓
User (Interactive dashboard)
```

## Technology Stack

### Core Technologies

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Frontend** | Streamlit | Interactive web interface |
| **Visualization** | Matplotlib, Plotly, Seaborn | Charts and graphs |
| **Data Processing** | Pandas, NumPy | Data manipulation |
| **Analysis** | SciPy, NetworkX | Statistical analysis, network graphs |
| **API Clients** | yfinance, fredapi, pandas-datareader | Financial data |
| **Database** | SQLite | Lightweight persistence |
| **Configuration** | Pydantic, python-dotenv | Type-safe config |
| **Testing** | pytest, pytest-cov | Test framework |
| **Code Quality** | Black, Ruff | Linting and formatting |
| **CI/CD** | Pre-commit hooks | Automated checks |

### Infrastructure

```
Development:
  • Python 3.9+ virtual environment
  • SQLite database
  • File-based logging
  • Local streamlit server

Production:
  • Docker containerization
  • Docker Compose orchestration
  • Health check endpoints
  • Volume mounts for data persistence

Cloud Deployment (Streamlit Cloud):
  • Automatic GitHub integration
  • Encrypted secrets management
  • Auto-scaling
  • HTTPS by default
```

## Data Models

### 1. Valuation Model (DCF)

```python
Inputs:
  - ticker: str
  - start_date: str
  - end_date: str
  - peers: List[str]
  - dcf_overrides: Dict[str, float]

Processing:
  1. Fetch financial data (yfinance)
  2. Calculate WACC (beta, risk-free rate, market premium)
  3. Project cash flows (10-year horizon)
  4. Calculate terminal value
  5. Discount to present value

Outputs:
  - enterprise_value: float
  - equity_value: float
  - equity_value_per_share: float
  - comps: DataFrame (peer comparisons)
```

### 2. Risk Model (VaR)

```python
Inputs:
  - ticker: str
  - start_date: str
  - end_date: str
  - confidence_levels: [0.95, 0.99]
  - shock_pct: float

Processing:
  1. Fetch historical prices
  2. Calculate returns distribution
  3. Compute VaR (historical, variance-covariance)
  4. Run stress tests

Outputs:
  - var_results: Dict[str, Dict[str, float]]
  - stress_results: Dict[str, float]
  - visualizations: matplotlib figures
```

### 3. Supply Chain Model

```python
Inputs:
  - supplier_relationships: List[Tuple[str, str]]

Processing:
  1. Build directed graph (NetworkX)
  2. Calculate centrality metrics
  3. Identify chokepoints (high betweenness)
  4. Analyze connectivity

Outputs:
  - metrics: DataFrame (node centrality scores)
  - chokepoints: List[str] (critical nodes)
  - graph: NetworkX DiGraph
```

### 4. Database Schema

```sql
-- Valuation history
CREATE TABLE valuation_runs (
    id INTEGER PRIMARY KEY,
    ticker TEXT,
    start_date TEXT,
    end_date TEXT,
    peers TEXT,  -- JSON array
    dcf_value REAL,
    equity_value REAL,
    equity_value_per_share REAL,
    timestamp TEXT,
    user_inputs TEXT  -- JSON
);

-- API call logs
CREATE TABLE api_calls (
    id INTEGER PRIMARY KEY,
    api_name TEXT,
    endpoint TEXT,
    status_code INTEGER,
    response_time_ms INTEGER,
    success BOOLEAN,
    error_message TEXT,
    timestamp TEXT
);

-- User interactions
CREATE TABLE user_interactions (
    id INTEGER PRIMARY KEY,
    session_id TEXT,
    action TEXT,
    ticker TEXT,
    parameters TEXT,  -- JSON
    timestamp TEXT
);

-- Error logs
CREATE TABLE error_logs (
    id INTEGER PRIMARY KEY,
    error_type TEXT,
    error_message TEXT,
    stack_trace TEXT,
    context TEXT,  -- JSON
    ticker TEXT,
    timestamp TEXT
);
```

## Security & Performance

### Security

1. **API Key Management**
   - Stored in `.env` (local) or Streamlit secrets (cloud)
   - Never committed to version control
   - Encrypted at rest (Streamlit Cloud)

2. **Input Validation**
   - Ticker symbol validation
   - Date range validation
   - Peer selection limits

3. **Rate Limiting**
   - Per-API throttling (60 calls/min, 1000 calls/hour)
   - Exponential backoff on errors
   - Request queuing

### Performance

1. **Caching Strategy**
   ```python
   @st.cache_data(ttl=300)  # 5 minutes
   def fetch_price_data(ticker, start, end):
       # Cached for 5 minutes per unique ticker/date combo

   @st.cache_data(ttl=3600)  # 1 hour
   def fetch_macro_data(end):
       # Macro data changes slowly
   ```

2. **Lazy Loading**
   - Components load only when needed
   - Heavy computations deferred until user input
   - Background tasks for non-critical updates

3. **Database Optimization**
   - Indexed queries (ticker, timestamp)
   - Efficient connection pooling
   - Periodic vacuuming

## Deployment Modes

### Mode 1: Local Development
```
Python + venv → SQLite → Local files
```

### Mode 2: Docker
```
Docker Container → Volume mounts → Persistent data
```

### Mode 3: Streamlit Cloud (Production)
```
GitHub → Streamlit Cloud → Ephemeral storage + secrets
```

## Extension Points

The architecture supports future enhancements:

### Phase 2: ML/AI Integration
```
[FinBERT NLP] → SEC Risk Scoring
[LightGBM] → Probabilistic Revenue Forecasting
[Monte Carlo] → DCF Distribution
```

### Phase 3: Data Engineering
```
[TimescaleDB] → Time-series optimization
[Redis] → Distributed caching
[APScheduler] → Background jobs
[Qdrant] → Vector embeddings
```

### Phase 4: Monetization
```
[Firebase Auth] → User management
[Stripe] → Payment processing
[FastAPI] → REST API layer
```

## Testing Strategy

```
Unit Tests (pytest)
    ├── Backend modules (strategic_alpha/tests/)
    │   • test_valuation.py
    │   • test_risk.py
    │   • test_supply.py
    │   • test_macro.py
    │   • test_sec.py
    │
    └── Dashboard infrastructure (sal_dashboard/tests/)
        • test_database.py
        • test_health.py
        • test_rate_limiter.py

Integration Tests
    • End-to-end valuation pipeline
    • Dashboard user workflows

Coverage
    • Strategic Alpha Backend: 52.72%
    • SAL Dashboard: 41.10%
    • Total: 57 tests passing
```

## Monitoring & Observability

```
Logs (logs/)
    ├── dashboard.log (INFO+)
    └── errors.log (ERROR+)

Database (data/database/dashboard.db)
    ├── API call metrics
    ├── User interaction patterns
    └── Error tracking

Health Checks (Admin Tab)
    ├── Database connectivity
    ├── Directory permissions
    ├── Disk space
    └── Application metrics
```

## Future Architecture Vision

```
                    ┌──────────────┐
                    │  Load Balancer│
                    └───────┬───────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │Streamlit │  │Streamlit │  │Streamlit │
        │Instance 1│  │Instance 2│  │Instance 3│
        └─────┬────┘  └─────┬────┘  └─────┬────┘
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                    ┌──────────────┐
                    │   Redis      │
                    │   (Cache)    │
                    └───────┬──────┘
                            │
                    ┌───────┴──────┐
              ┌─────▼─────┐  ┌─────▼─────┐
              │PostgreSQL │  │ Qdrant    │
              │(TimescaleDB)│(Embeddings)│
              └───────────┘  └───────────┘
```

---

**Document Version**: 1.0
**Last Updated**: November 2024
**Maintained By**: Strategic Alpha Suite Team
