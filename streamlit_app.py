"""
Streamlit App for HY-IG Spread Indicator Analysis Dashboard
Deploy to Streamlit Cloud: https://streamlit.io/cloud
"""
import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

# Page configuration
st.set_page_config(
    page_title="HY-IG Spread Indicator Analysis",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #667eea;
    }
    </style>
""", unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    """Load all JSON data files"""
    base_path = Path(__file__).parent
    
    try:
        with open(base_path / "data" / "hyig_data.json", "r") as f:
            monthly_data = json.load(f)
    except FileNotFoundError:
        st.error("❌ data/hyig_data.json not found. Please run fetch_data.py first.")
        st.stop()
    
    try:
        with open(base_path / "outputs" / "analysis_summary.json", "r") as f:
            analysis_data = json.load(f)
    except FileNotFoundError:
        st.warning("⚠️ outputs/analysis_summary.json not found. Some sections will be unavailable.")
        analysis_data = None
    
    try:
        with open(base_path / "outputs" / "strategy_backtest.json", "r") as f:
            strategy_data = json.load(f)
    except FileNotFoundError:
        st.warning("⚠️ outputs/strategy_backtest.json not found. Strategy sections will be unavailable.")
        strategy_data = None
    
    return monthly_data, analysis_data, strategy_data

# Header
st.markdown("""
    <div class="main-header">
        <h1>📊 HY-IG Spread Indicator: Analysis & Investment Strategy</h1>
        <p>High Yield vs Investment Grade Option-Adjusted Spread Analysis (1993-Present)</p>
    </div>
""", unsafe_allow_html=True)

# Load data
monthly_data, analysis_data, strategy_data = load_data()

# Sidebar
with st.sidebar:
    st.header("📋 Navigation")
    sections = [
        "Overview",
        "Key Findings Summary",
        "Correlation Analysis",
        "Lead-Lag Analysis",
        "Causality Testing",
        "Predictive Modeling",
        "Regime Analysis",
        "Investment Strategy"
    ]
    selected_section = st.radio("Select Section", sections)

# Overview Section
if selected_section == "Overview":
    st.header("📈 Overview")
    
    if monthly_data and monthly_data.get("stats"):
        stats = monthly_data["stats"]
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Spread", f"{stats['spread_mean']:.2f} bps")
        with col2:
            st.metric("Std Dev", f"{stats['spread_std']:.2f} bps")
        with col3:
            st.metric("Min", f"{stats['spread_min']:.2f} bps")
        with col4:
            st.metric("Max", f"{stats['spread_max']:.2f} bps")
    
    # Time series chart
    if monthly_data and monthly_data.get("monthly"):
        dates = pd.to_datetime(monthly_data["monthly"]["dates"])
        spreads = [v if v != "null" else None for v in monthly_data["monthly"]["hy_ig_spread"]]
        returns = [v if v != "null" else None for v in monthly_data["monthly"]["spy_returns"]]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=dates, y=spreads, name="HY-IG Spread (bps)", line=dict(color="#667eea")),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=dates, y=returns, name="SPY Returns (%)", line=dict(color="#28a745")),
            secondary_y=True
        )
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="HY-IG Spread (bps)", secondary_y=False)
        fig.update_yaxes(title_text="SPY Returns (%)", secondary_y=True)
        fig.update_layout(height=500, title="HY-IG Spread vs S&P 500 Returns Over Time")
        st.plotly_chart(fig, use_container_width=True)

# Key Findings Summary (spread metrics only - aligned with local dashboard)
elif selected_section == "Key Findings Summary":
    st.header("🔍 Key Findings Summary")
    st.caption("Spread distribution metrics (HY-IG spread in basis points). Strategy performance is in the Investment Strategy section.")
    
    if monthly_data and monthly_data.get("stats"):
        stats = monthly_data["stats"]
        st.subheader("HY-IG Spread Statistics")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Mean Spread", f"{stats['spread_mean']:.2f} bps")
            st.metric("Std Deviation", f"{stats['spread_std']:.2f} bps")
        with col2:
            st.metric("Minimum", f"{stats['spread_min']:.2f} bps")
            st.metric("Maximum", f"{stats['spread_max']:.2f} bps")
        with col3:
            st.metric("25th Percentile", f"{stats['spread_p25']:.2f} bps")
            st.metric("Median (50th)", f"{stats['spread_p50']:.2f} bps")
        with col4:
            st.metric("75th Percentile", f"{stats['spread_p75']:.2f} bps")
            st.metric("90th Percentile", f"{stats['spread_p90']:.2f} bps")
    else:
        st.warning("Spread statistics not available. Run fetch_data.py to load hyig_data.json.")

# Correlation Analysis (scatter chart + summary - aligned with local dashboard)
elif selected_section == "Correlation Analysis":
    st.header("🔗 Step 2: Correlation Analysis")
    
    if monthly_data and monthly_data.get("monthly"):
        dates = monthly_data["monthly"]["dates"]
        spreads = [float(v) if v != "null" and v is not None else None for v in monthly_data["monthly"]["hy_ig_spread"]]
        returns = [float(v) if v != "null" and v is not None else None for v in monthly_data["monthly"]["spy_returns"]]
        valid = [(s, r) for s, r in zip(spreads, returns) if s is not None and r is not None]
        if valid:
            xs, ys = zip(*valid)
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="Monthly Data", marker=dict(size=5, opacity=0.6)))
            fig.update_layout(
                title="HY-IG Spread vs SPY Monthly Returns",
                xaxis_title="HY-IG Spread (bps)",
                yaxis_title="SPY Monthly Return (%)",
                height=500,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("No valid data for correlation scatter.")
    else:
        st.warning("Monthly data not available. Run fetch_data.py.")
    
    if analysis_data and analysis_data.get("correlation_summary"):
        cs = analysis_data["correlation_summary"]
        st.subheader("Correlation Summary")
        st.write(f"**Level correlation (spread vs returns):** {cs.get('level_correlation', 'N/A'):.3f}" if isinstance(cs.get('level_correlation'), (int, float)) else "N/A")
        st.write(f"**Number of significant lags:** {cs.get('n_significant', 'N/A')}")

# Lead-Lag Analysis
elif selected_section == "Lead-Lag Analysis":
    st.header("⏱️ Step 3: Lead-Lag Analysis")
    
    if analysis_data and analysis_data.get("lead_lag"):
        ll = analysis_data["lead_lag"]
        best_lag = ll.get("best_lag", "N/A")
        best_corr = ll.get("best_correlation", ll.get("max_correlation"))
        st.write(f"**Best Lag:** {best_lag} month(s)")
        st.write(f"**Best Correlation at Optimal Lag:** {best_corr:.4f}" if isinstance(best_corr, (int, float)) else f"**Max Correlation:** {best_corr}")
        interp = "leads" if (isinstance(best_lag, (int, float)) and best_lag > 0) else ("lags" if isinstance(best_lag, (int, float)) and best_lag < 0 else "is contemporaneous with")
        lags_abs = abs(int(best_lag)) if isinstance(best_lag, (int, float)) else 0
        st.write(f"**Interpretation:** The HY-IG spread {interp} SPY returns by {lags_abs} month(s).")

# Causality Testing
elif selected_section == "Causality Testing":
    st.header("🔬 Step 4: Causality Testing (Granger Causality)")
    
    st.write("Granger causality tests whether the HY-IG spread helps predict SPY returns beyond what past SPY returns can predict.")
    if analysis_data and analysis_data.get("lead_lag"):
        st.write(f"**Optimal Lag (from lead-lag analysis):** {analysis_data['lead_lag'].get('best_lag', 'N/A')} month(s)")
    st.caption("Detailed causality test results require running the full analysis script.")

# Predictive Modeling
elif selected_section == "Predictive Modeling":
    st.header("🤖 Step 5: Predictive Modeling")
    
    if analysis_data and analysis_data.get("predictive_modeling"):
        pm = analysis_data["predictive_modeling"]
        st.write(f"**Mean R²:** {pm.get('mean_r2', pm.get('r2_score', 'N/A')):.4f}" if isinstance(pm.get('mean_r2', pm.get('r2_score')), (int, float)) else "N/A")
        if pm.get("top_features"):
            st.write("**Top features:** " + ", ".join(pm["top_features"]))
        interp = pm.get("mean_r2", 0)
        if isinstance(interp, (int, float)) and interp < 0:
            st.caption("Negative R² indicates the model performs worse than a simple mean predictor; the relationship may require non-linear or regime-specific approaches.")

# Regime Analysis (HY-IG Spread Over Time + optional regime stats - aligned with local)
elif selected_section == "Regime Analysis":
    st.header("📊 Step 6: Regime Analysis")
    
    if monthly_data and monthly_data.get("monthly"):
        dates = pd.to_datetime(monthly_data["monthly"]["dates"])
        spreads = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["hy_ig_spread"]]
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=spreads, mode="lines", name="HY-IG Spread", line=dict(color="#667eea")))
        fig.update_layout(
            title="HY-IG Spread Over Time",
            xaxis_title="Date",
            yaxis_title="Spread (bps)",
            height=500,
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("Monthly data not available. Run fetch_data.py.")
    
    if strategy_data and strategy_data.get("performance_metrics", {}).get("regime_stats"):
        regime_stats = strategy_data["performance_metrics"]["regime_stats"]
        st.subheader("Performance by Regime")
        regimes = []
        strategy_returns = []
        spy_returns = []
        for regime, stats in regime_stats.items():
            regimes.append(regime)
            strategy_returns.append(stats.get("('Strategy_Return', 'mean')", 0))
            spy_returns.append(stats.get("('SPY_Returns', 'mean')", 0))
        fig = go.Figure()
        fig.add_trace(go.Bar(x=regimes, y=strategy_returns, name="Strategy Return", marker_color="#667eea"))
        fig.add_trace(go.Bar(x=regimes, y=spy_returns, name="SPY Return", marker_color="#28a745"))
        fig.update_layout(title="Average Monthly Returns by Regime", xaxis_title="Regime", yaxis_title="Return (%)", height=400, barmode="group")
        st.plotly_chart(fig, use_container_width=True)

# Investment Strategy (full section - aligned with local dashboard)
elif selected_section == "Investment Strategy":
    st.header("💰 Investment Strategy: Backtested Implementation (1993–Present)")
    
    if not strategy_data:
        st.warning("Strategy data not available. Please run strategy_backtest.py first.")
        st.stop()
    
    metrics = strategy_data.get("performance_metrics", {})
    data = strategy_data.get("monthly_data")
    
    # Strategy Framework & Percentile Methodology
    st.subheader("Strategy Framework")
    st.markdown("""
    **Rolling Window Approach:** The strategy uses a **rolling 60-month (5-year) window** to calculate percentile thresholds for HY-IG spread classification.
    - For each month, the system looks back at the **previous 60 months** of HY-IG spread data.
    - It calculates P25, P50, P75, P90 from this rolling window and classifies the current month's spread.
    - Position size: **100% SPY** (≤P25), **75%** (P25–P50), **50%** (P50–P75), **25%** (P75–P90), **10%** (>P90).
    """)
    
    # Strategy Framework Table with current percentile ranges
    st.subheader("Strategy Framework Table")
    if monthly_data and monthly_data.get("stats"):
        stats = monthly_data["stats"]
        framework_df = pd.DataFrame([
            {"Spread Regime": "Low Spread (Buy)", "Percentile Range": "≤ 25th", "Current Range (bps)": f"≤ {stats['spread_p25']:.2f}", "Position Size": "100% SPY", "Rationale": "Favorable credit conditions, full equity exposure"},
            {"Spread Regime": "Moderate-Low Spread", "Percentile Range": "25th–50th", "Current Range (bps)": f"{stats['spread_p25']:.2f}–{stats['spread_p50']:.2f}", "Position Size": "75% SPY", "Rationale": "Moderate risk, slight reduction"},
            {"Spread Regime": "Moderate-High Spread", "Percentile Range": "50th–75th", "Current Range (bps)": f"{stats['spread_p50']:.2f}–{stats['spread_p75']:.2f}", "Position Size": "50% SPY", "Rationale": "Elevated risk, defensive positioning"},
            {"Spread Regime": "High Spread (Caution)", "Percentile Range": "75th–90th", "Current Range (bps)": f"{stats['spread_p75']:.2f}–{stats['spread_p90']:.2f}", "Position Size": "25% SPY", "Rationale": "High credit stress, significant reduction"},
            {"Spread Regime": "Very High Spread (Reduce)", "Percentile Range": "> 90th", "Current Range (bps)": f"> {stats['spread_p90']:.2f}", "Position Size": "10% SPY", "Rationale": "Severe stress, minimal exposure"},
        ])
        st.dataframe(framework_df, use_container_width=True, hide_index=True)
    
    # Performance Metrics (SPY vs Strategy vs Outperformance)
    st.subheader("Performance Metrics")
    if metrics.get("spy") and metrics.get("strategy") and metrics.get("outperformance"):
        perf_df = pd.DataFrame([
            {"Metric": "Total Return", "SPY": f"{metrics['spy']['total_return']:.2f}%", "Strategy": f"{metrics['strategy']['total_return']:.2f}%", "Outperformance": f"{metrics['outperformance']['total_return']:.2f}%"},
            {"Metric": "Annualized Return", "SPY": f"{metrics['spy']['annualized_return']:.2f}%", "Strategy": f"{metrics['strategy']['annualized_return']:.2f}%", "Outperformance": f"{metrics['outperformance']['annualized_return']:.2f}%"},
            {"Metric": "Sharpe Ratio", "SPY": f"{metrics['spy']['sharpe_ratio']:.2f}", "Strategy": f"{metrics['strategy']['sharpe_ratio']:.2f}", "Outperformance": f"+{metrics['outperformance']['sharpe_improvement']:.2f}"},
            {"Metric": "Max Drawdown", "SPY": f"{metrics['spy']['max_drawdown']:.2f}%", "Strategy": f"{metrics['strategy']['max_drawdown']:.2f}%", "Outperformance": f"{metrics['outperformance']['max_dd_improvement']:.2f}% improvement"},
            {"Metric": "Win Rate", "SPY": f"{metrics['spy']['win_rate']:.1f}%", "Strategy": f"{metrics['strategy']['win_rate']:.1f}%", "Outperformance": "-"},
        ])
        st.dataframe(perf_df, use_container_width=True, hide_index=True)
    
    # Strategy Implementation Timeline
    if data:
        dates = pd.to_datetime(data["dates"])
        spreads = [float(v) if v not in ("null", None) else None for v in data["spread"]]
        positions = [float(v) if v not in ("null", None) else None for v in data.get("position_size", [])]
        fed_funds = [float(v) if v not in ("null", None) else None for v in data.get("fedfunds", [])]
        
        st.subheader("Strategy Implementation Timeline")
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(go.Scatter(x=dates, y=spreads, name="HY-IG Spread (bps)", line=dict(color="#667eea")), secondary_y=False)
        fig.add_trace(go.Scatter(x=dates, y=positions, name="Position Size", line=dict(color="#28a745"), mode="lines+markers"), secondary_y=True)
        if fed_funds and any(f is not None for f in fed_funds):
            fig.add_trace(go.Scatter(x=dates, y=fed_funds, name="Fed Funds Rate (%)", line=dict(color="#ff6b6b")), secondary_y=True)
        if strategy_data.get("fed_rate_periods"):
            for period in strategy_data["fed_rate_periods"]:
                if period.get("type") == "increase":
                    fig.add_vrect(x0=period["start"], x1=period["end"], fillcolor="rgba(255, 192, 203, 0.2)", layer="below", line_width=0)
                elif period.get("type") == "decrease":
                    fig.add_vrect(x0=period["start"], x1=period["end"], fillcolor="rgba(144, 238, 144, 0.2)", layer="below", line_width=0)
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="HY-IG Spread (bps)", secondary_y=False)
        fig.update_yaxes(title_text="Position Size / Fed %", secondary_y=True)
        fig.update_layout(height=600, title="Spread and Position Size Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # Cumulative Returns (use spy_cumulative, strategy_cumulative)
        st.subheader("Cumulative Returns Comparison")
        cum_spy = data.get("spy_cumulative") or data.get("cumulative_spy")
        cum_strat = data.get("strategy_cumulative") or data.get("cumulative_strategy")
        if cum_spy and cum_strat:
            cum_spy = [float(v) if v not in ("null", None) else None for v in cum_spy]
            cum_strat = [float(v) if v not in ("null", None) else None for v in cum_strat]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=cum_spy, name="SPY Buy & Hold", line=dict(color="#667eea", width=2)))
            fig.add_trace(go.Scatter(x=dates, y=cum_strat, name="Strategy", line=dict(color="#28a745", width=2)))
            if strategy_data.get("fed_rate_periods"):
                for period in strategy_data["fed_rate_periods"]:
                    if period.get("type") == "increase":
                        fig.add_vrect(x0=period["start"], x1=period["end"], fillcolor="rgba(255, 192, 203, 0.2)", layer="below", line_width=0)
                    elif period.get("type") == "decrease":
                        fig.add_vrect(x0=period["start"], x1=period["end"], fillcolor="rgba(144, 238, 144, 0.2)", layer="below", line_width=0)
            fig.update_layout(height=600, title="Cumulative Returns: Strategy vs Buy & Hold", xaxis_title="Date", yaxis_title="Cumulative Return (multiple)")
            st.plotly_chart(fig, use_container_width=True)
        
        # Drawdown Analysis
        st.subheader("Drawdown Analysis")
        dd_spy = data.get("spy_drawdown")
        dd_strat = data.get("strategy_drawdown")
        if dd_spy and dd_strat:
            dd_spy = [float(v) if v not in ("null", None) else None for v in dd_spy]
            dd_strat = [float(v) if v not in ("null", None) else None for v in dd_strat]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=dd_spy, name="SPY Drawdown", fill="tozeroy", line=dict(color="#667eea")))
            fig.add_trace(go.Scatter(x=dates, y=dd_strat, name="Strategy Drawdown", fill="tozeroy", line=dict(color="#28a745")))
            fig.update_layout(height=500, title="Drawdown Analysis", xaxis_title="Date", yaxis_title="Drawdown (%)", hovermode="x unified")
            st.plotly_chart(fig, use_container_width=True)
    
    # Current Strategy Review (past 1 year - array of {date, regime, spread, position_size, action, has_action})
    if strategy_data.get("current_strategy_review"):
        st.subheader("Current Strategy Review (Past 1 Year)")
        review = strategy_data["current_strategy_review"]
        if isinstance(review, list) and review:
            review_df = pd.DataFrame(review)
            cols = [c for c in ["date", "regime", "spread", "position_size", "action"] if c in review_df.columns]
            if cols:
                st.dataframe(review_df[cols].head(12), use_container_width=True, hide_index=True)
        else:
            st.caption("No review data.")
    
    # FRED Funds Rate Impact Analysis (full table + commentary)
    if metrics.get("fed_rate_periods"):
        st.subheader("FRED Funds Rate Impact Analysis")
        fed_metrics = metrics["fed_rate_periods"]
        period_labels = {"increase": "Rate Increase Periods", "decrease": "Rate Decrease Periods", "none": "No Change Periods", "rate_above_2.5": "Fed Funds Rate ≥ 2.5%", "rate_below_2.5": "Fed Funds Rate < 2.5%"}
        rows = []
        for key in ["increase", "decrease", "none", "rate_above_2.5", "rate_below_2.5"]:
            if fed_metrics.get(key):
                m = fed_metrics[key]
                rows.append({
                    "Period": period_labels.get(key, key),
                    "Months": m["n_months"],
                    "Strategy Return": f"{m['strategy']['annualized_return']:.2f}%",
                    "SPY Return": f"{m['spy']['annualized_return']:.2f}%",
                    "Strategy Sharpe": f"{m['strategy']['sharpe_ratio']:.2f}",
                    "SPY Sharpe": f"{m['spy']['sharpe_ratio']:.2f}",
                    "Strategy Max DD": f"{m['strategy']['max_drawdown']:.2f}%",
                    "SPY Max DD": f"{m['spy']['max_drawdown']:.2f}%",
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        if fed_metrics.get("increase") and fed_metrics.get("decrease"):
            inc = fed_metrics["increase"]["strategy"]
            dec = fed_metrics["decrease"]["strategy"]
            st.markdown("**Key findings:** Strategy performance by rate environment (return, Sharpe, drawdown) supports using the HY-IG spread as a regime filter; defensive sizing in high-spread periods improves risk-adjusted results.")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>HY-IG Spread Indicator Analysis Dashboard | Generated: {}</p>
        <p>Data Source: FRED (BAMLH0A0HYM2, BAMLC0A0CM) & Yahoo Finance (SPY)</p>
    </div>
""".format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)
