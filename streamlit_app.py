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

# Key Findings Summary
elif selected_section == "Key Findings Summary":
    st.header("🔍 Key Findings Summary")
    
    if analysis_data:
        findings = analysis_data.get("summary", {})
        
        col1, col2 = st.columns(2)
        with col1:
            if "correlation" in findings:
                st.metric("Correlation", f"{findings['correlation']:.3f}")
            if "lead_lag" in findings:
                st.metric("Optimal Lag", f"{findings['lead_lag']} month(s)")
        with col2:
            if "granger_causality" in findings:
                st.metric("Granger Causality", "Significant" if findings.get("granger_causality") else "Not Significant")
            if "predictive_r2" in findings:
                st.metric("Predictive R²", f"{findings['predictive_r2']:.3f}")
    
    if strategy_data and strategy_data.get("performance_metrics"):
        st.subheader("Strategy Performance")
        metrics = strategy_data["performance_metrics"]
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Strategy Return", f"{metrics['strategy']['annualized_return']:.2f}%")
        with col2:
            st.metric("SPY Return", f"{metrics['spy']['annualized_return']:.2f}%")
        with col3:
            st.metric("Strategy Sharpe", f"{metrics['strategy']['sharpe_ratio']:.2f}")
        with col4:
            st.metric("Max Drawdown", f"{metrics['strategy']['max_drawdown']:.2f}%")

# Correlation Analysis
elif selected_section == "Correlation Analysis":
    st.header("🔗 Correlation Analysis")
    
    if analysis_data and analysis_data.get("correlation"):
        corr = analysis_data["correlation"]
        st.write(f"**Pearson Correlation:** {corr.get('pearson', {}).get('correlation', 'N/A'):.3f}")
        st.write(f"**P-value:** {corr.get('pearson', {}).get('p_value', 'N/A'):.4f}")
        
        if corr.get("correlation_by_regime"):
            st.subheader("Correlation by Regime")
            regime_df = pd.DataFrame(corr["correlation_by_regime"])
            st.dataframe(regime_df, use_container_width=True)

# Lead-Lag Analysis
elif selected_section == "Lead-Lag Analysis":
    st.header("⏱️ Lead-Lag Analysis")
    
    if analysis_data and analysis_data.get("lead_lag"):
        ll = analysis_data["lead_lag"]
        st.write(f"**Best Lag:** {ll.get('best_lag', 'N/A')} month(s)")
        st.write(f"**Max Correlation:** {ll.get('max_correlation', 'N/A'):.3f}")
        
        if ll.get("lag_correlations"):
            lags = list(ll["lag_correlations"].keys())
            corrs = list(ll["lag_correlations"].values())
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=lags, y=corrs, mode='lines+markers', name='Correlation'))
            fig.update_layout(title="Correlation vs Lag", xaxis_title="Lag (months)", yaxis_title="Correlation", height=400)
            st.plotly_chart(fig, use_container_width=True)

# Causality Testing
elif selected_section == "Causality Testing":
    st.header("🔬 Granger Causality Testing")
    
    if analysis_data and analysis_data.get("granger_causality"):
        gc = analysis_data["granger_causality"]
        st.write(f"**Test Result:** {'Significant' if gc.get('significant', False) else 'Not Significant'}")
        st.write(f"**P-value:** {gc.get('p_value', 'N/A'):.4f}")
        st.write(f"**Interpretation:** {gc.get('interpretation', 'N/A')}")

# Predictive Modeling
elif selected_section == "Predictive Modeling":
    st.header("🤖 Predictive Modeling")
    
    if analysis_data and analysis_data.get("predictive_modeling"):
        pm = analysis_data["predictive_modeling"]
        st.write(f"**Model Type:** {pm.get('model_type', 'N/A')}")
        st.write(f"**R² Score:** {pm.get('r2_score', 'N/A'):.3f}")
        st.write(f"**RMSE:** {pm.get('rmse', 'N/A'):.3f}")
        
        if pm.get("feature_importance"):
            st.subheader("Feature Importance")
            fi_df = pd.DataFrame(pm["feature_importance"])
            st.dataframe(fi_df, use_container_width=True)

# Regime Analysis
elif selected_section == "Regime Analysis":
    st.header("📊 Regime Analysis")
    
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
        fig.update_layout(title="Average Monthly Returns by Regime", xaxis_title="Regime", yaxis_title="Return (%)", height=400, barmode='group')
        st.plotly_chart(fig, use_container_width=True)

# Investment Strategy
elif selected_section == "Investment Strategy":
    st.header("💰 Investment Strategy: Backtested Implementation")
    
    if not strategy_data:
        st.warning("Strategy data not available. Please run strategy_backtest.py first.")
        st.stop()
    
    metrics = strategy_data.get("performance_metrics", {})
    
    # Performance Metrics
    st.subheader("Performance Metrics")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Return", f"{metrics['strategy']['total_return']:.2f}%")
    with col2:
        st.metric("Annualized Return", f"{metrics['strategy']['annualized_return']:.2f}%")
    with col3:
        st.metric("Sharpe Ratio", f"{metrics['strategy']['sharpe_ratio']:.2f}")
    with col4:
        st.metric("Max Drawdown", f"{metrics['strategy']['max_drawdown']:.2f}%")
    
    # Strategy Implementation Timeline
    if strategy_data.get("monthly_data"):
        st.subheader("Strategy Implementation Timeline")
        data = strategy_data["monthly_data"]
        dates = pd.to_datetime(data["dates"])
        spreads = [v if v != "null" else None for v in data["spread"]]
        positions = [v if v != "null" else None for v in data.get("position_size", [])]
        fed_funds = [v if v != "null" else None for v in data.get("fedfunds", [])]
        
        fig = make_subplots(specs=[[{"secondary_y": True}]])
        fig.add_trace(
            go.Scatter(x=dates, y=spreads, name="HY-IG Spread", line=dict(color="#667eea")),
            secondary_y=False
        )
        fig.add_trace(
            go.Scatter(x=dates, y=positions, name="Position Size", line=dict(color="#dc3545"), mode='lines+markers'),
            secondary_y=True
        )
        if fed_funds and any(f is not None for f in fed_funds):
            fig.add_trace(
                go.Scatter(x=dates, y=fed_funds, name="Fed Funds Rate (%)", line=dict(color="#ffc107"), yaxis="y3"),
                secondary_y=False
            )
        
        # Add Fed rate period backgrounds
        if strategy_data.get("fed_rate_periods"):
            for period in strategy_data["fed_rate_periods"]:
                if period.get("type") == "increase":
                    fig.add_vrect(
                        x0=period["start"], x1=period["end"],
                        fillcolor="rgba(255, 192, 203, 0.3)", layer="below", line_width=0
                    )
                elif period.get("type") == "decrease":
                    fig.add_vrect(
                        x0=period["start"], x1=period["end"],
                        fillcolor="rgba(144, 238, 144, 0.3)", layer="below", line_width=0
                    )
        
        fig.update_xaxes(title_text="Date")
        fig.update_yaxes(title_text="HY-IG Spread (bps)", secondary_y=False)
        fig.update_yaxes(title_text="Position Size", secondary_y=True)
        fig.update_layout(height=600, title="Spread and Position Size Over Time")
        st.plotly_chart(fig, use_container_width=True)
        
        # Cumulative Returns
        st.subheader("Cumulative Returns Comparison")
        if data.get("cumulative_strategy") and data.get("cumulative_spy"):
            cum_strategy = [v if v != "null" else None for v in data["cumulative_strategy"]]
            cum_spy = [v if v != "null" else None for v in data["cumulative_spy"]]
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=cum_strategy, name="Strategy", line=dict(color="#667eea", width=2)))
            fig.add_trace(go.Scatter(x=dates, y=cum_spy, name="SPY", line=dict(color="#28a745", width=2)))
            
            # Add Fed rate period backgrounds
            if strategy_data.get("fed_rate_periods"):
                for period in strategy_data["fed_rate_periods"]:
                    if period.get("type") == "increase":
                        fig.add_vrect(
                            x0=period["start"], x1=period["end"],
                            fillcolor="rgba(255, 192, 203, 0.3)", layer="below", line_width=0
                        )
                    elif period.get("type") == "decrease":
                        fig.add_vrect(
                            x0=period["start"], x1=period["end"],
                            fillcolor="rgba(144, 238, 144, 0.3)", layer="below", line_width=0
                        )
            
            fig.update_layout(height=600, title="Cumulative Returns: Strategy vs SPY", xaxis_title="Date", yaxis_title="Cumulative Return (%)")
            st.plotly_chart(fig, use_container_width=True)
        
        # FRED Rate Impact Analysis
        if metrics.get("fed_rate_periods"):
            st.subheader("Performance by FRED Funds Rate Change Periods")
            fed_metrics = metrics["fed_rate_periods"]
            
            period_data = []
            for period_type in ["increase", "decrease", "none", "rate_above_2.5", "rate_below_2.5"]:
                if fed_metrics.get(period_type):
                    m = fed_metrics[period_type]
                    period_data.append({
                        "Period": period_type.replace("_", " ").title(),
                        "Months": m["n_months"],
                        "Strategy Return": f"{m['strategy']['annualized_return']:.2f}%",
                        "SPY Return": f"{m['spy']['annualized_return']:.2f}%",
                        "Strategy Sharpe": f"{m['strategy']['sharpe_ratio']:.2f}",
                        "Strategy Max DD": f"{m['strategy']['max_drawdown']:.2f}%"
                    })
            
            if period_data:
                st.dataframe(pd.DataFrame(period_data), use_container_width=True)
        
        # Current Strategy Review
        if strategy_data.get("current_strategy_review"):
            st.subheader("Current Strategy Review (Past 1 Year)")
            review = strategy_data["current_strategy_review"]
            
            if review.get("recent_actions"):
                for action in review["recent_actions"][:12]:  # Show last 12 months
                    st.write(f"**{action.get('date', 'N/A')}:** {action.get('regime', 'N/A')} - {action.get('action', 'N/A')}")

# Footer
st.markdown("---")
st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>HY-IG Spread Indicator Analysis Dashboard | Generated: {}</p>
        <p>Data Source: FRED (BAMLH0A0HYM2, BAMLC0A0CM) & Yahoo Finance (SPY)</p>
    </div>
""".format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)
