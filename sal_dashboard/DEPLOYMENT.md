# Strategic Alpha Dashboard - Deployment Guide

## Phase 2 Production Features

This document describes the production-ready features added in Phase 2.

## ✅ Implemented Features

### 1. Rate Limiting & API Throttling
- **Location**: `src/rate_limiter.py`
- **Features**:
  - Per-API rate limiting (60 calls/minute, 1000 calls/hour by default)
  - Exponential backoff on rate limit errors
  - Thread-safe request queuing
  - Automatic retry with backoff
- **Usage**: Automatically applied to yfinance API calls

### 2. Comprehensive Logging
- **Location**: `src/logging_config.py`
- **Features**:
  - Structured logging with file rotation (10MB, 5 backups)
  - Separate error log file
  - Performance timing context manager
  - Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Files**: 
  - `logs/dashboard.log` - General logs
  - `logs/errors.log` - Error logs only

### 3. Secrets Management
- **Location**: `src/secrets_manager.py`
- **Features**:
  - Streamlit secrets integration for deployed apps
  - Environment variable fallback for local development
  - Automatic validation of required secrets
- **Usage**: API keys are automatically retrieved from secrets or `.env`

### 4. Database Integration
- **Location**: `src/database.py`
- **Features**:
  - SQLite database for historical tracking
  - Tracks: valuation runs, API calls, user interactions, errors
  - Database file: `data/database/dashboard.db`
- **Tables**:
  - `valuation_runs` - Historical valuation calculations
  - `api_calls` - API call logs with performance metrics
  - `user_interactions` - User action tracking
  - `error_logs` - Error tracking with stack traces

### 5. Docker Deployment
- **Files**: `Dockerfile`, `docker-compose.yml`, `.dockerignore`
- **Features**:
  - Multi-stage build for smaller image size
  - Health checks built-in
  - Volume mounts for data persistence
  - Environment variable support

### 6. Health Checks & Monitoring
- **Location**: `src/health.py`, Admin tab in dashboard
- **Features**:
  - System health checks (database, directories, disk space)
  - Application metrics (API calls, success rates, response times)
  - Valuation history viewer
  - Real-time monitoring dashboard

## 🚀 Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# 1. Create .env file from template
cp .env.example .env
# Edit .env with your API keys

# 2. Build and run
docker-compose up -d

# 3. View logs
docker-compose logs -f

# 4. Stop
docker-compose down
```

### Option 2: Docker (Standalone)

```bash
# 1. Build image
docker build -t strategic-alpha-dashboard .

# 2. Run container
docker run -d \
  -p 8501:8501 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/logs:/app/logs \
  -e FRED_API_KEY=your_key \
  -e SEC_API_KEY=your_key \
  strategic-alpha-dashboard

# 3. View logs
docker logs -f strategic-alpha-dashboard
```

### Option 3: Streamlit Cloud (Recommended for Portfolio/Demo)

**Step-by-Step Guide:**

1. **Prepare Repository**
   ```bash
   # Ensure all changes are committed
   git add .
   git commit -m "chore: prepare for Streamlit Cloud deployment"
   git push origin main
   ```

2. **Connect to Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io/)
   - Sign in with GitHub
   - Click "New app"
   - Select your repository: `your-username/Stock-Finder`
   - Main file path: `sal_dashboard/app/streamlit_app.py`
   - App URL: Choose a custom URL (e.g., `strategic-alpha-suite`)

3. **Configure Secrets**
   - Click "Advanced settings" > "Secrets"
   - Use the format from `.streamlit/secrets.toml.example`
   - Paste your secrets configuration:

   ```toml
   [api_keys]
   fred_api_key = "your_actual_fred_key"
   sec_api_key = "your_actual_sec_key"

   [settings]
   shock_pct = -0.10
   risk_peer_tickers = ["AMD", "AVGO", "TSM", "ASML", "INTC"]
   supply_shock_tickers = ["TSM", "ASML"]
   ```

4. **Deploy!**
   - Click "Deploy"
   - Wait 2-3 minutes for initial deployment
   - Your app will be live at: `https://your-app-name.streamlit.app`

5. **Share Your Work**
   - Add the live URL to your resume
   - Include in LinkedIn profile: "View Live Demo"
   - Share in GitHub README with a badge

**Important Notes:**
- Streamlit Cloud provides free hosting for public repositories
- Apps sleep after inactivity (wake up on first access)
- API keys are encrypted and never exposed
- The app works without API keys but with sample data

### Option 4: Local Development

```bash
# 1. Activate virtual environment
source venv/bin/activate  # or: .venv/bin/activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 4. Run
streamlit run app/streamlit_app.py
```

## 📊 Monitoring & Maintenance

### Viewing Logs

```bash
# Dashboard logs
tail -f logs/dashboard.log

# Error logs
tail -f logs/errors.log

# Docker logs
docker-compose logs -f dashboard
```

### Database Queries

```bash
# Connect to SQLite database
sqlite3 data/database/dashboard.db

# Example queries
SELECT COUNT(*) FROM valuation_runs;
SELECT * FROM api_calls ORDER BY timestamp DESC LIMIT 10;
SELECT * FROM error_logs ORDER BY timestamp DESC LIMIT 10;
```

### Health Check

Access the **Admin** tab in the dashboard to view:
- System health status
- Application metrics
- Recent valuation history
- API call statistics

## 🔒 Security Best Practices

1. **Never commit `.env` file** - It's in `.gitignore`
2. **Use Streamlit secrets** for production deployments
3. **Rotate API keys** regularly
4. **Monitor error logs** for suspicious activity
5. **Limit API rate limits** in production if needed

## 📈 Performance Tuning

### Rate Limiting

Adjust rate limits in `streamlit_app.py`:

```python
rate_limiter = get_rate_limiter(
    max_calls_per_minute=60,  # Adjust as needed
    max_calls_per_hour=1000,   # Adjust as needed
)
```

### Caching

Caching is already implemented with TTL:
- Price data: 5 minutes
- Macro data: 1 hour
- Supply chain: 30 minutes
- Valuation: 5 minutes
- Risk: 30 minutes

### Database Maintenance

The SQLite database will grow over time. Consider:
- Periodic backups
- Archiving old data
- Vacuuming the database

```bash
sqlite3 data/database/dashboard.db "VACUUM;"
```

## 🐛 Troubleshooting

### Database Locked Errors
- Ensure only one instance is writing to the database
- Check for stale database connections

### Rate Limit Errors
- Increase rate limit thresholds
- Check API provider limits
- Review cached data usage

### Health Check Failures
- Check directory permissions
- Verify disk space
- Review error logs

## 📝 Next Steps (Phase 3)

Potential enhancements:
- PostgreSQL migration for better concurrency
- Redis caching layer
- Prometheus metrics integration
- Alerting system
- Automated backups
- User authentication
- API endpoint for programmatic access

