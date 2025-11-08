"""
Streamlit application providing an interactive view of strategic alpha analytics.
"""

from __future__ import annotations

# ============================================================================
# STANDARD LIBRARY IMPORTS - Must come first
# ============================================================================
import re
import sys
import time
import traceback
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable

# ============================================================================
# PATH SETUP - CRITICAL: Must happen BEFORE importing from 'app' or 'src'
# ============================================================================
# Add sal_dashboard directory to Python path so 'app' and 'src' packages
# can be imported. This MUST be done before any imports from those packages.
sal_dashboard_dir = Path(__file__).resolve().parent.parent
if str(sal_dashboard_dir) not in sys.path:
    sys.path.insert(0, str(sal_dashboard_dir))

# ============================================================================
# THIRD-PARTY IMPORTS
# ============================================================================
import pandas as pd
import streamlit as st
import yfinance as yf

# ============================================================================
# LOCAL IMPORTS - Must come AFTER path setup above
# ============================================================================
# DO NOT MOVE THESE IMPORTS ABOVE THE PATH SETUP - they will fail!
from app.components.charts import dcf_heatmap, macro_chart, price_chart, risk_histogram
from app.components.kpi_cards import render_kpi_cards
from app.components.tables import format_chokepoints, format_comps
from src import macro, risk, supply, valuation
from src.config import ROOT_DIR, get_settings
from src.database import get_db
from src.health import check_health, get_metrics
from src.logging_config import get_logger, setup_logging
from src.rate_limiter import get_rate_limiter


def _format_dollar(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "NA"
    if abs(value) >= 1_000_000_000:
        return f"${value/1_000_000_000:.1f}B"
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:.1f}M"
    return f"${value:,.0f}"


@st.cache_data(ttl=300)  # 5 minute cache for price data
def _fetch_quote_info(ticker: str) -> Dict[str, float | str]:
    """Safely request ticker fundamentals from yfinance with rate limiting."""
    logger = get_logger(__name__)
    db = get_db()
    rate_limiter = get_rate_limiter()

    start_time = time.time()
    try:
        # Use rate limiter for API call
        info = rate_limiter.call(
            "yfinance",
            lambda: yf.Ticker(ticker).info or {},
            max_retries=2
        )

        response_time = int((time.time() - start_time) * 1000)
        db.log_api_call(
            api_name="yfinance",
            endpoint=f"info/{ticker}",
            status_code=200,
            response_time_ms=response_time,
            success=True,
        )

        # Validate that we got meaningful data
        if not info or len(info) < 5:
            st.warning(
                f"⚠️ Limited data available for {ticker}. Some metrics may be unavailable.")
            logger.warning("Limited data for ticker %s: %d fields",
                           ticker, len(info) if info else 0)
    except (KeyError, AttributeError, ValueError) as e:
        # Specific exceptions for yfinance data issues
        response_time = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        db.log_api_call(
            api_name="yfinance",
            endpoint=f"info/{ticker}",
            response_time_ms=response_time,
            success=False,
            error_message=error_msg,
        )
        logger.error("Failed to fetch quote info for %s: %s",
                     ticker, error_msg)
        st.error(f"❌ Failed to fetch quote info for {ticker}: {error_msg}")
        info = {}
    except Exception as e:
        # Catch-all for network errors, API failures, etc.
        response_time = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        db.log_api_call(
            api_name="yfinance",
            endpoint=f"info/{ticker}",
            response_time_ms=response_time,
            success=False,
            error_message=error_msg,
        )
        db.log_error(
            error_type=type(e).__name__,
            error_message=error_msg,
            stack_trace=traceback.format_exc(),
            ticker=ticker,
        )
        logger.error("Failed to fetch quote info for %s: %s",
                     ticker, error_msg, exc_info=True)
        st.error(f"❌ Failed to fetch quote info for {ticker}: {error_msg}")
        info = {}
    return info


def _last_12m(prices: pd.Series) -> pd.Series:
    if prices.empty:
        return prices
    cutoff = prices.index.max() - pd.DateOffset(months=12)
    return prices[prices.index >= cutoff]


def _dcf_override_inputs(base_inputs: Any) -> Dict[str, float]:
    col1, col2, col3 = st.columns(3)
    col4, col5, col6 = st.columns(3)

    revenue_growth = col1.number_input(
        "Revenue Growth %",
        value=base_inputs.revenue_growth * 100,
        format="%.2f",
    )
    ebit_margin = col2.number_input(
        "EBIT Margin %",
        value=base_inputs.ebit_margin * 100,
        format="%.2f",
    )
    tax_rate = col3.number_input(
        "Tax Rate %",
        value=base_inputs.tax_rate * 100,
        format="%.2f",
    )
    reinvestment = col4.number_input(
        "Reinvestment Rate %",
        value=base_inputs.reinvestment_rate * 100,
        format="%.2f",
    )
    wacc = col5.number_input(
        "WACC %",
        value=base_inputs.wacc * 100,
        format="%.2f",
    )
    terminal_growth = col6.number_input(
        "Terminal Growth %",
        value=base_inputs.terminal_growth * 100,
        format="%.2f",
    )

    return {
        "revenue_growth": revenue_growth / 100,
        "ebit_margin": ebit_margin / 100,
        "tax_rate": tax_rate / 100,
        "reinvestment_rate": reinvestment / 100,
        "wacc": wacc / 100,
        "terminal_growth": terminal_growth / 100,
    }


def _report_content(
    ticker: str,
    macro_result: Any,
    supply_df: pd.DataFrame,
    dcf_result: Dict[str, Any],
    comps_table: pd.DataFrame,
    risk_summary: Dict[str, Dict[str, float]],
    dcf_overrides: Dict[str, float],
    peers: Iterable[str],
) -> str:
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC")
    metrics = macro_result.metrics
    historical = risk_summary["historical"]
    variance_covariance = risk_summary["variance_covariance"]
    stress = risk_summary["stress"]

    overrides_text = "\n".join(
        f"- {key.replace('_', ' ').title()}: {value * 100:.2f}%"
        for key, value in dcf_overrides.items()
    )

    report = f"""# {ticker.upper()} Dashboard Memo

Generated: {timestamp}

## Macro Context
- CPI YoY: {metrics['cpi_yoy']:.2f}%
- Unemployment Rate: {metrics['unemployment_rate']:.2f}%
- Fed Funds Rate: {metrics['fed_funds_rate']:.2f}%
- Industrial Production YoY: {metrics['industrial_production_yoy']:.2f}%

## Supply Chain Highlights
Top chokepoints:

{supply_df.to_markdown(index=False)}

Artifacts:
- Supply metrics CSV: artifacts/supply_metrics.csv (downloadable within app)

## Valuation
- DCF intrinsic value / share: ${dcf_result['equity_value_per_share']:.2f}
- Enterprise value (model): {_format_dollar(dcf_result['enterprise_value'])}
- Equity value (model): {_format_dollar(dcf_result['equity_value'])}
- Peer set: {', '.join(peers)}

Applied DCF overrides:
{overrides_text}

Relative comps:

{comps_table.to_markdown(index=False)}

## Risk
- Historical VaR 95%: {historical['var_95']:.4f}
- Historical VaR 99%: {historical['var_99']:.4f}
- Variance-Covariance VaR 95%: {variance_covariance['var_95']:.4f}
- Variance-Covariance VaR 99%: {variance_covariance['var_99']:.4f}
- Stress shock applied: {stress['shock_pct']:.2%}
- Portfolio loss under stress: {stress['portfolio_loss']:.2%}

## Notes
- Live data attempts rely on yfinance and FRED; missing credentials trigger cached sample usage.
- Supply network derived from sample edges mimicking GPU supplier stack.
- Report generated by `sal_dashboard` Streamlit interface.
"""
    return report


def _validate_ticker(ticker: str) -> bool:
    """Validate ticker symbol format."""
    if not ticker or len(ticker) == 0:
        return False
    # Basic validation: 1-5 uppercase letters/numbers, no spaces
    pattern = r'^[A-Z0-9]{1,5}$'
    return bool(re.match(pattern, ticker.upper()))


def _validate_date_range(start_date: date, end_date: date) -> tuple[bool, str]:
    """Validate date range inputs."""
    if start_date >= end_date:
        return False, "Start date must be before end date."
    if end_date > date.today():
        return False, "End date cannot be in the future."
    # Check for reasonable range (not too old, not too short)
    max_range_days = 365 * 10  # 10 years
    min_range_days = 30  # 1 month
    range_days = (end_date - start_date).days
    if range_days > max_range_days:
        return False, f"Date range cannot exceed {max_range_days // 365} years."
    if range_days < min_range_days:
        return False, f"Date range must be at least {min_range_days} days."
    return True, ""


def _validate_peers(peers: list[str]) -> tuple[bool, str]:
    """Validate peer ticker list."""
    if not peers:
        return False, "At least one peer must be selected."
    for peer in peers:
        if not _validate_ticker(peer):
            return False, f"Invalid ticker symbol: {peer}"
    return True, ""


@st.cache_data(ttl=3600)  # 1 hour cache for macro data (updates daily)
def _cached_load_macro_snapshot(end: str) -> Any:
    """Cached wrapper for macro snapshot loading."""
    settings = get_settings()
    return macro.load_macro_snapshot(end=end, settings=settings)


@st.cache_data(ttl=1800)  # 30 min cache for supply analysis
def _cached_load_supply_analysis() -> Any:
    """Cached wrapper for supply analysis loading."""
    settings = get_settings()
    return supply.load_supply_analysis(settings)


@st.cache_data(ttl=300)  # 5 minute cache for price data
def _cached_base_dcf_inputs(ticker: str, start: str, end: str) -> tuple[Any, Any]:
    """Cached wrapper for DCF base inputs."""
    return valuation.base_dcf_inputs(ticker, start, end)


@st.cache_data(ttl=300)  # 5 minute cache for valuation results
def _cached_load_valuation_result(
    ticker: str, start: str, end: str, peers: tuple[str, ...]
) -> Any:
    """Cached wrapper for valuation result loading."""
    settings = get_settings()
    return valuation.load_valuation_result(
        ticker=ticker, start=start, end=end, peers=list(peers), settings=settings
    )


@st.cache_data(ttl=1800)  # 30 min cache for risk analysis
def _cached_load_risk_result(
    ticker: str, start: str, end: str, shock_pct: float
) -> Any:
    """Cached wrapper for risk result loading."""
    settings = get_settings()
    return risk.load_risk_result(
        ticker=ticker, start=start, end=end, shock_pct=shock_pct, settings=settings
    )


def main() -> None:
    # Initialize logging
    setup_logging(log_level="INFO", log_to_file=True, log_to_console=False)
    logger = get_logger(__name__)
    logger.info("Starting Strategic Alpha Dashboard")

    # Initialize database
    db = get_db()

    # Initialize rate limiter
    rate_limiter = get_rate_limiter(
        max_calls_per_minute=60, max_calls_per_hour=1000)

    st.set_page_config(page_title="Strategic Alpha Dashboard", layout="wide")
    st.title("Strategic Alpha Dashboard")

    settings = get_settings()

    # Get session ID for tracking
    if "session_id" not in st.session_state:
        import uuid
        st.session_state.session_id = str(uuid.uuid4())
        logger.info("New session started: %s", st.session_state.session_id)

    st.sidebar.header("Controls")
    ticker_input = st.sidebar.text_input("Ticker", value="NVDA")
    ticker = ticker_input.strip().upper()

    # Input validation
    if not _validate_ticker(ticker):
        logger.warning("Invalid ticker entered: %s", ticker)
        db.log_user_interaction(
            action="invalid_ticker",
            session_id=st.session_state.session_id,
            ticker=ticker,
        )
        st.sidebar.error(
            "❌ Invalid ticker symbol. Please enter a valid ticker (1-5 letters/numbers).")
        st.stop()

    default_start = date.today() - timedelta(days=365 * 2)
    default_end = date.today()
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(default_start, default_end),
        help="Historical window for price, valuation, and risk analytics.",
    )
    if not isinstance(date_range, tuple) or len(date_range) != 2:
        st.sidebar.error("❌ Please select a valid start and end date.")
        st.stop()
    start_date, end_date = date_range
    start_str, end_str = start_date.isoformat(), end_date.isoformat()

    # Log user interaction
    db.log_user_interaction(
        action="ticker_selected",
        session_id=st.session_state.session_id,
        ticker=ticker,
        parameters={"start_date": start_str, "end_date": end_str},
    )

    # Validate date range
    is_valid_date, date_error = _validate_date_range(start_date, end_date)
    if not is_valid_date:
        st.sidebar.error(f"❌ {date_error}")
        st.stop()

    default_peers = settings.risk_peer_tickers
    peer_selection = st.sidebar.multiselect(
        "Peer Set",
        options=sorted(set(default_peers + [ticker])),
        default=[peer for peer in default_peers if peer != ticker],
        help="Select peers for comps and risk benchmarking.",
    )
    if ticker not in peer_selection:
        peer_selection = [ticker] + peer_selection

    # Validate peers
    is_valid_peers, peer_error = _validate_peers(peer_selection)
    if not is_valid_peers:
        st.sidebar.error(f"❌ {peer_error}")
        st.stop()

    shock_pct = st.sidebar.slider(
        "Shock %",
        min_value=-30.0,
        max_value=-5.0,
        value=-10.0,
        step=0.5,
        help="Apply to foundry-exposed names in stress test.",
    )

    # Load backend analytics with error handling and loading indicators
    try:
        with st.spinner("📊 Loading macro economic data..."):
            macro_result = _cached_load_macro_snapshot(end=end_str)
            macro_df = macro.macro_dataframe(macro_result)
    except Exception as e:  # noqa: BLE001 - Broad exception handling for user-friendly errors
        st.error(f"❌ Failed to load macro data: {str(e)}")
        st.info("💡 The app will continue with limited functionality. Please check your FRED API key or try again later.")
        st.stop()

    try:
        with st.spinner("🔗 Analyzing supply chain network..."):
            supply_result = _cached_load_supply_analysis()
            supply_metrics_df = supply.supply_metrics(supply_result)
            chokepoints_df = supply.chokepoints_table(supply_result)
    except Exception as e:  # noqa: BLE001 - Broad exception handling for user-friendly errors
        st.error(f"❌ Failed to load supply chain analysis: {str(e)}")
        st.info("💡 Supply chain data may be unavailable. Please check your data files.")
        # Create empty dataframes as fallback
        supply_metrics_df = pd.DataFrame()
        chokepoints_df = pd.DataFrame()
        supply_result = None

    try:
        with st.spinner(f"💰 Loading valuation data for {ticker}..."):
            price_series, base_inputs = _cached_base_dcf_inputs(
                ticker, start_str, end_str
            )
            if price_series.empty:
                st.warning(
                    f"⚠️ No price data found for {ticker} in the selected date range.")
    except Exception as e:  # noqa: BLE001 - Broad exception handling for user-friendly errors
        st.error(f"❌ Failed to load price data for {ticker}: {str(e)}")
        st.info(
            "💡 Please verify the ticker symbol is correct and the date range is valid.")
        st.stop()

    try:
        with st.spinner("📈 Computing valuation metrics..."):
            valuation_result = _cached_load_valuation_result(
                ticker=ticker,
                start=start_str,
                end=end_str,
                peers=tuple(peer_selection),  # Convert to tuple for caching
            )
            comps_df = valuation_result.comps
    except Exception as e:  # noqa: BLE001 - Broad exception handling for user-friendly errors
        st.error(f"❌ Failed to compute valuation: {str(e)}")
        st.info(
            "💡 Valuation calculation failed. Please check your inputs and try again.")
        st.stop()

    try:
        dcf_overrides = _dcf_override_inputs(base_inputs)
        overridden_inputs = valuation.override_dcf_inputs(
            base_inputs, dcf_overrides
        )
        dcf_result = valuation.run_dcf_model(overridden_inputs)

        # Save valuation run to database
        db.save_valuation_run(
            ticker=ticker,
            start_date=start_str,
            end_date=end_str,
            peers=peer_selection,
            dcf_value=sum(dcf_result.get("present_value", {}).values()
                          ) + dcf_result.get("terminal_value", 0),
            equity_value=dcf_result.get("equity_value", 0),
            equity_value_per_share=dcf_result.get("equity_value_per_share", 0),
            user_inputs=dcf_overrides,
        )
    except Exception as e:  # noqa: BLE001 - Broad exception handling for user-friendly errors
        error_msg = str(e)
        db.log_error(
            error_type=type(e).__name__,
            error_message=error_msg,
            stack_trace=traceback.format_exc(),
            context={"ticker": ticker, "dcf_overrides": dcf_overrides},
            ticker=ticker,
        )
        logger.error("DCF calculation failed for %s: %s",
                     ticker, error_msg, exc_info=True)
        st.error(f"❌ Failed to run DCF model: {error_msg}")
        st.info("💡 DCF calculation failed. Please check your input parameters.")
        st.stop()

    try:
        with st.spinner("⚡ Computing risk metrics..."):
            risk_result = _cached_load_risk_result(
                ticker=ticker,
                start=start_str,
                end=end_str,
                shock_pct=shock_pct / 100,
            )
            risk_details = risk.risk_summary(risk_result)
            portfolio_returns = risk.portfolio_returns(risk_result)
    except Exception as e:  # noqa: BLE001 - Broad exception handling for user-friendly errors
        st.error(f"❌ Failed to compute risk metrics: {str(e)}")
        st.info("💡 Risk analysis failed. Please check your inputs and peer selection.")
        # Create fallback risk details
        risk_details = {
            "historical": {"var_95": 0.0, "var_99": 0.0},
            "variance_covariance": {"var_95": 0.0, "var_99": 0.0},
            "stress": {"shock_pct": shock_pct / 100, "portfolio_loss": 0.0},
        }
        portfolio_returns = pd.Series(dtype=float)

    with st.spinner("📊 Fetching current quote information..."):
        info = _fetch_quote_info(ticker)
    kpi_labels = ["Market Cap", "Enterprise Value", "P/E", "EBITDA Margin"]
    kpi_values = [
        _format_dollar(info.get("marketCap")),
        _format_dollar(info.get("enterpriseValue") or info.get("marketCap")),
        f"{info.get('trailingPE', float('nan')):.2f}" if info.get(
            "trailingPE") else "NA",
        f"{info.get('ebitdaMargins', float('nan'))*100:.2f}%" if info.get(
            "ebitdaMargins") else "NA",
    ]

    overview_tab, macro_tab, supply_tab, valuation_tab, risk_tab, report_tab, admin_tab = st.tabs(
        ["Overview", "Macro Context", "Supply Map",
            "Valuation", "Risk", "Report", "Admin"]
    )

    with overview_tab:
        render_kpi_cards(kpi_labels, kpi_values)
        st.subheader("Price Performance")
        st.plotly_chart(price_chart(_last_12m(price_series)),
                        use_container_width=True)

    with macro_tab:
        st.plotly_chart(macro_chart(macro_df), use_container_width=True)
        st.info(macro.macro_commentary(macro_result.metrics))

    with supply_tab:
        if supply_result is None or chokepoints_df.empty:
            st.warning(
                "⚠️ Supply chain data is unavailable. Please check your data files.")
        else:
            st.plotly_chart(
                supply.supply_graph_figure(supply_result), use_container_width=True
            )
            st.dataframe(format_chokepoints(chokepoints_df),
                         use_container_width=True)
            if not supply_metrics_df.empty:
                st.download_button(
                    label="Download Supply Metrics CSV",
                    data=supply.metrics_csv_bytes(supply_metrics_df),
                    file_name="supply_metrics.csv",
                    mime="text/csv",
                )

    with valuation_tab:
        st.subheader("Discounted Cash Flow")
        cols = st.columns(3)
        cols[0].metric("PV of Cash Flows", _format_dollar(
            sum(dcf_result["present_value"].values())))
        cols[1].metric(
            "Terminal Value",
            _format_dollar(dcf_result["terminal_value"]),
        )
        cols[2].metric(
            "Equity Value / Share",
            f"${dcf_result['equity_value_per_share']:.2f}",
        )
        st.plotly_chart(dcf_heatmap(
            dcf_result["sensitivity"]), use_container_width=True)

        st.subheader("Relative Comps")
        st.dataframe(format_comps(comps_df), use_container_width=True)
        percentiles = valuation.peer_percentiles(comps_df, ticker)
        st.caption(
            "Percentile positioning vs. peers "
            f"(P/E: {percentiles['pe']!s}, EV/EBITDA: {percentiles['ev_ebitda']!s}, P/S: {percentiles['ps']!s})"
        )

    with risk_tab:
        st.subheader("Value at Risk")
        hist = risk_details["historical"]
        varcov = risk_details["variance_covariance"]
        stress_info = risk_details["stress"]

        st.write(
            pd.DataFrame(
                {
                    "Method": ["Historical", "Historical", "Variance-Covariance", "Variance-Covariance"],
                    "Confidence": ["95%", "99%", "95%", "99%"],
                    "VaR": [
                        hist["var_95"],
                        hist["var_99"],
                        varcov["var_95"],
                        varcov["var_99"],
                    ],
                }
            )
        )
        st.write(
            f"Stress shock {stress_info['shock_pct']:.2%} → portfolio impact {stress_info['portfolio_loss']:.2%}"
        )
        st.plotly_chart(risk_histogram(portfolio_returns),
                        use_container_width=True)

    with report_tab:
        st.subheader("Generate Markdown Report")
        formatted_chokepoints = format_chokepoints(chokepoints_df)[
            ["node", "country", "betweenness"]
        ]
        formatted_comps = format_comps(comps_df)[
            ["ticker", "price", "pe", "ev_ebitda", "ps"]
        ]
        report_text = _report_content(
            ticker=ticker,
            macro_result=macro_result,
            supply_df=formatted_chokepoints,
            dcf_result=dcf_result,
            comps_table=formatted_comps,
            risk_summary=risk_details,
            dcf_overrides=dcf_overrides,
            peers=[p for p in peer_selection if p != ticker],
        )
        if st.button("Save Report"):
            report_path = ROOT_DIR / "reports" / \
                f"{ticker.upper()}_dashboard_memo.md"
            report_path.write_text(report_text, encoding="utf-8")
            st.success(f"Report written to {report_path}")
        st.download_button(
            "Download Markdown",
            data=report_text.encode("utf-8"),
            file_name=f"{ticker.upper()}_dashboard_memo.md",
            mime="text/markdown",
        )

    with admin_tab:
        st.subheader("System Health & Metrics")

        if st.button("Refresh Health Check"):
            st.rerun()

        # Health check
        with st.spinner("Checking system health..."):
            health = check_health()
            metrics = get_metrics()

        # Health status
        status_color = {
            "healthy": "🟢",
            "degraded": "🟡",
            "unhealthy": "🔴",
        }
        status_icon = status_color.get(health["status"], "⚪")
        st.metric("Overall Status",
                  f"{status_icon} {health['status'].upper()}")

        # Health checks details
        st.subheader("Health Checks")
        for check_name, check_data in health["checks"].items():
            if isinstance(check_data, dict) and "status" in check_data:
                check_status = check_data.get("status", "unknown")
                check_icon = status_color.get(check_status, "⚪")
                with st.expander(f"{check_icon} {check_name.replace('_', ' ').title()}"):
                    st.json(check_data)
            else:
                with st.expander(f"{check_name.replace('_', ' ').title()}"):
                    st.json(check_data)

        # Metrics
        st.subheader("Application Metrics (Last 24 Hours)")
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("API Calls", metrics.get("api_calls_24h", 0))
        col2.metric("Success Rate",
                    f"{metrics.get('api_success_rate', 0):.1f}%")
        col3.metric("Avg Response Time",
                    f"{metrics.get('avg_api_response_time_ms', 0):.0f} ms")
        col4.metric("Total Valuation Runs",
                    metrics.get("total_valuation_runs", 0))

        # Valuation history
        st.subheader("Recent Valuation History")
        history = db.get_valuation_history(limit=20)
        if history:
            history_df = pd.DataFrame(history)
            # Format columns for display
            display_cols = ["ticker", "timestamp",
                            "dcf_value", "equity_value_per_share"]
            if all(col in history_df.columns for col in display_cols):
                st.dataframe(
                    history_df[display_cols].rename(columns={
                        "ticker": "Ticker",
                        "timestamp": "Timestamp",
                        "dcf_value": "DCF Value",
                        "equity_value_per_share": "Equity Value/Share",
                    }),
                    use_container_width=True,
                )
        else:
            st.info("No valuation history available yet.")


if __name__ == "__main__":
    main()
