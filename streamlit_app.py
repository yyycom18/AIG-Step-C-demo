"""
AIG Consolidated Dashboard: Indicator vs ETF Studies (Step C)
Projects: VIX1M/3M vs SPY (Project02), HY-IG Spread vs SPY (Project03)
Deploy to Streamlit Cloud: https://streamlit.io/cloud
"""
import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
from datetime import datetime

# Study options: (display name, study id)
STUDY_OPTIONS = [
    ("VIX1M/3M vs SPY (Project 02)", "p02"),
    ("HY-IG Spread vs SPY (Project 03)", "p03"),
]

# Page configuration
st.set_page_config(
    page_title="AIG Indicator Studies",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
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
    .metric-card { background: #f8f9fa; padding: 1rem; border-radius: 5px; border-left: 4px solid #667eea; }
    </style>
""", unsafe_allow_html=True)

# Paths: app lives in Project03; Project02 may be sibling or under cwd
PROJECT03_PATH = Path(__file__).resolve().parent


def _project02_base():
    """Resolve Project02 base path: try sibling of Project03, then cwd, then cwd/Project02."""
    candidates = [
        PROJECT03_PATH.parent / "Project02",   # sibling: .../Cursor/Project02
        Path.cwd() / "Project02",              # e.g. run from Cursor -> Cursor/Project02
        Path.cwd(),                            # if cwd is already Project02
        PROJECT03_PATH / "Project02",          # Project02 inside Project03 (alternate layout)
    ]
    for base in candidates:
        if base is not None and (base / "data" / "vix_data.json").exists():
            return base
    return PROJECT03_PATH.parent / "Project02"  # fallback for error messages


@st.cache_data
def load_data(study: str):
    """Load data for selected study. study in ('p02', 'p03')."""
    if study == "p03":
        base = PROJECT03_PATH
        try:
            with open(base / "data" / "hyig_data.json", "r") as f:
                monthly_data = json.load(f)
        except FileNotFoundError:
            return None, None, None
        try:
            with open(base / "outputs" / "analysis_summary.json", "r") as f:
                analysis_data = json.load(f)
        except FileNotFoundError:
            analysis_data = None
        try:
            with open(base / "outputs" / "strategy_backtest.json", "r") as f:
                strategy_data = json.load(f)
        except FileNotFoundError:
            strategy_data = None
        return monthly_data, analysis_data, strategy_data

    if study == "p02":
        # Try standard layout: Project02 as sibling (or under cwd)
        base = _project02_base()
        vix_path = base / "data" / "vix_data.json"
        # Fallback: Streamlit Cloud when repo root is Project03 – use Project03/data_p02/vix_data.json
        alt_path = PROJECT03_PATH / "data_p02" / "vix_data.json"
        path_to_try = vix_path if vix_path.exists() else alt_path
        try:
            with open(path_to_try, "r") as f:
                vix_data = json.load(f)
        except FileNotFoundError:
            return None, None, None
        except Exception:
            return None, None, None
        return vix_data, None, None

    return None, None, None


def compute_spy_returns_from_prices(spy_prices):
    """Compute monthly returns (%) from SPY price series. Returns list same length; first element None."""
    out = [None]
    for i in range(1, len(spy_prices)):
        p0 = spy_prices[i - 1]
        p1 = spy_prices[i]
        if p0 is None or p1 is None or p0 == "null" or p1 == "null" or float(p0) == 0:
            out.append(None)
        else:
            try:
                r = (float(p1) - float(p0)) / float(p0) * 100
                out.append(r)
            except (TypeError, ValueError):
                out.append(None)
    return out


# Initialize session state for study selection
if "study" not in st.session_state:
    st.session_state["study"] = "p03"

# Sidebar: Home + section list
with st.sidebar:
    st.header("📋 Navigation")
    sections = [
        "Home",
        "Overview",
        "Key Findings Summary",
        "Correlation Analysis",
        "Lead-Lag Analysis",
        "Causality Testing",
        "Predictive Modeling",
        "Regime Analysis",
        "Investment Strategy",
    ]
    selected_section = st.radio("Select Section", sections)

    # Study selector (only when not on Home, so user can switch study)
    if selected_section != "Home":
        st.divider()
        st.subheader("Study")
        study_labels = [o[0] for o in STUDY_OPTIONS]
        study_ids = [o[1] for o in STUDY_OPTIONS]
        idx = study_ids.index(st.session_state["study"]) if st.session_state["study"] in study_ids else 0
        new_study = st.radio(
            "Indicator vs ETF",
            study_labels,
            index=idx,
            key="study_radio",
        )
        new_id = study_ids[study_labels.index(new_study)]
        if new_id != st.session_state["study"]:
            st.session_state["study"] = new_id
            st.rerun()
        st.caption(f"Current: {study_labels[study_ids.index(st.session_state['study'])]}")

study = st.session_state["study"]
monthly_data, analysis_data, strategy_data = load_data(study)

# ---- Home ----
if selected_section == "Home":
    st.markdown("""
        <div class="main-header">
            <h1>📊 AIG Indicator Studies (Step C)</h1>
            <p>Consolidated dashboard: choose an indicator vs ETF study to view analysis and strategy.</p>
        </div>
    """, unsafe_allow_html=True)

    st.subheader("Choose a study")
    st.write("Select the indicator vs ETF study below to open its dashboard sections (Overview, Key Findings, Correlation, Regime, Investment Strategy, etc.).")

    choice = st.radio(
        "Study",
        [o[0] for o in STUDY_OPTIONS],
        key="home_study",
    )
    study_id = next(s[1] for s in STUDY_OPTIONS if s[0] == choice)

    if st.button("Open this study"):
        st.session_state["study"] = study_id
        st.rerun()

    st.divider()
    st.markdown("""
        - **VIX1M/3M vs SPY (Project 02):** VIX 1-month / 3-month ratio vs S&P 500 (SPY).
        - **HY-IG Spread vs SPY (Project 03):** High Yield minus Investment Grade OAS vs SPY.
        Both follow the same structural study (Overview, Key Findings, Correlation, Lead-Lag, Causality, Predictive, Regime, Investment Strategy).
    """)
    st.markdown("---")
    st.caption(f"AIG Group | Generated {datetime.now().strftime('%Y-%m-%d')}")
    st.stop()

# After Home: require a study and (for p03) at least monthly_data
if monthly_data is None:
    if study == "p02":
        tried_std = _project02_base() / "data" / "vix_data.json"
        tried_alt = PROJECT03_PATH / "data_p02" / "vix_data.json"
        st.warning(
            "**Data not found for Project 02.** "
            "On **Streamlit Cloud** (app root = Project03), copy `Project02/data/vix_data.json` to **`Project03/data_p02/vix_data.json`**, commit, and redeploy. "
            "See `Project03/data_p02/README.md` for steps."
        )
        st.caption(f"Paths checked: `{tried_std}` and `{tried_alt}`")
    else:
        st.warning("Data not found for Project 03. Ensure `data/hyig_data.json` exists (run `fetch_data.py` in Project03).")
    st.stop()

# Dynamic header by study
if study == "p03":
    st.markdown("""
        <div class="main-header">
            <h1>📊 HY-IG Spread vs SPY</h1>
            <p>High Yield vs Investment Grade OAS — Analysis & Investment Strategy (1993–Present)</p>
        </div>
    """, unsafe_allow_html=True)
else:
    st.markdown("""
        <div class="main-header">
            <h1>📊 VIX1M/3M vs SPY</h1>
            <p>VIX 1-Month / 3-Month Ratio — Fundamental Analysis for S&P Recovery (1993–Present)</p>
        </div>
    """, unsafe_allow_html=True)

# ---------- Overview ----------
if selected_section == "Overview":
    st.header("📈 Overview")

    if study == "p03":
        if monthly_data and monthly_data.get("stats"):
            s = monthly_data["stats"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean Spread", f"{s['spread_mean']:.2f} bps")
            with col2:
                st.metric("Std Dev", f"{s['spread_std']:.2f} bps")
            with col3:
                st.metric("Min", f"{s['spread_min']:.2f} bps")
            with col4:
                st.metric("Max", f"{s['spread_max']:.2f} bps")
        if monthly_data and monthly_data.get("monthly"):
            dates = pd.to_datetime(monthly_data["monthly"]["dates"])
            spreads = [v if v != "null" else None for v in monthly_data["monthly"]["hy_ig_spread"]]
            returns = [v if v != "null" else None for v in monthly_data["monthly"]["spy_returns"]]
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=dates, y=spreads, name="HY-IG Spread (bps)", line=dict(color="#667eea")), secondary_y=False)
            fig.add_trace(go.Scatter(x=dates, y=returns, name="SPY Returns (%)", line=dict(color="#28a745")), secondary_y=True)
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="HY-IG Spread (bps)", secondary_y=False)
            fig.update_yaxes(title_text="SPY Returns (%)", secondary_y=True)
            fig.update_layout(height=500, title="HY-IG Spread vs S&P 500 Returns Over Time")
            st.plotly_chart(fig, use_container_width=True)

    else:  # p02
        if monthly_data and monthly_data.get("stats"):
            s = monthly_data["stats"]
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Mean Ratio", f"{s['ratio_mean']:.3f}")
            with col2:
                st.metric("Std Dev", f"{s['ratio_std']:.3f}")
            with col3:
                st.metric("80th %ile", f"{s['ratio_p80']:.3f}")
            with col4:
                st.metric("90th %ile", f"{s['ratio_p90']:.3f}")
            with col5:
                st.metric("95th %ile", f"{s['ratio_p95']:.3f}")
        if monthly_data and monthly_data.get("monthly"):
            dates = pd.to_datetime(monthly_data["monthly"]["dates"])
            ratio = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["ratio"]]
            spy = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["spy"]]
            spy_ret = compute_spy_returns_from_prices(spy)
            n = len(dates)
            if len(spy_ret) != n:
                spy_ret = (spy_ret + [None] * n)[:n] if len(spy_ret) < n else spy_ret[:n]
            fig = make_subplots(specs=[[{"secondary_y": True}]])
            fig.add_trace(go.Scatter(x=dates, y=ratio, name="VIX1M/3M Ratio", line=dict(color="#667eea")), secondary_y=False)
            fig.add_trace(go.Scatter(x=dates, y=spy_ret, name="SPY Returns (%)", line=dict(color="#28a745")), secondary_y=True)
            fig.update_xaxes(title_text="Date")
            fig.update_yaxes(title_text="VIX1M/3M Ratio", secondary_y=False)
            fig.update_yaxes(title_text="SPY Returns (%)", secondary_y=True)
            fig.update_layout(height=500, title="VIX1M/3M Ratio vs S&P 500 Returns Over Time")
            st.plotly_chart(fig, use_container_width=True)

# ---------- Key Findings Summary ----------
elif selected_section == "Key Findings Summary":
    st.header("🔍 Key Findings Summary")

    if study == "p03":
        st.caption("Spread distribution metrics (HY-IG spread in basis points).")
        if monthly_data and monthly_data.get("stats"):
            s = monthly_data["stats"]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Mean Spread", f"{s['spread_mean']:.2f} bps")
                st.metric("Std Deviation", f"{s['spread_std']:.2f} bps")
            with col2:
                st.metric("Minimum", f"{s['spread_min']:.2f} bps")
                st.metric("Maximum", f"{s['spread_max']:.2f} bps")
            with col3:
                st.metric("25th Percentile", f"{s['spread_p25']:.2f} bps")
                st.metric("Median (50th)", f"{s['spread_p50']:.2f} bps")
            with col4:
                st.metric("75th Percentile", f"{s['spread_p75']:.2f} bps")
                st.metric("90th Percentile", f"{s['spread_p90']:.2f} bps")
        else:
            st.warning("Spread statistics not available.")
    else:
        st.caption("VIX1M/3M ratio distribution metrics.")
        if monthly_data and monthly_data.get("stats"):
            s = monthly_data["stats"]
            col1, col2, col3, col4, col5 = st.columns(5)
            with col1:
                st.metric("Mean Ratio", f"{s['ratio_mean']:.3f}")
            with col2:
                st.metric("Std Deviation", f"{s['ratio_std']:.3f}")
            with col3:
                st.metric("80th Percentile", f"{s['ratio_p80']:.3f}")
            with col4:
                st.metric("90th Percentile", f"{s['ratio_p90']:.3f}")
            with col5:
                st.metric("95th Percentile", f"{s['ratio_p95']:.3f}")
        else:
            st.warning("Ratio statistics not available.")

# ---------- Correlation Analysis ----------
elif selected_section == "Correlation Analysis":
    st.header("🔗 Step 2: Correlation Analysis")

    if study == "p03":
        if monthly_data and monthly_data.get("monthly"):
            dates = monthly_data["monthly"]["dates"]
            spreads = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["hy_ig_spread"]]
            returns = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["spy_returns"]]
            valid = [(s, r) for s, r in zip(spreads, returns) if s is not None and r is not None]
            if valid:
                xs, ys = zip(*valid)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="Monthly", marker=dict(size=5, opacity=0.6)))
                fig.update_layout(title="HY-IG Spread vs SPY Monthly Returns", xaxis_title="HY-IG Spread (bps)", yaxis_title="SPY Monthly Return (%)", height=500)
                st.plotly_chart(fig, use_container_width=True)
            if analysis_data and analysis_data.get("correlation_summary"):
                cs = analysis_data["correlation_summary"]
                st.write(f"**Level correlation:** {cs.get('level_correlation', 'N/A'):.3f}" if isinstance(cs.get('level_correlation'), (int, float)) else "N/A")
        else:
            st.warning("Monthly data not available.")
    else:
        if monthly_data and monthly_data.get("monthly"):
            dates = monthly_data["monthly"]["dates"]
            ratio = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["ratio"]]
            spy = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["spy"]]
            spy_ret = compute_spy_returns_from_prices(spy)
            n = len(dates)
            if len(spy_ret) != n:
                spy_ret = (spy_ret + [None] * n)[:n] if len(spy_ret) < n else spy_ret[:n]
            valid = [(r, s) for r, s in zip(ratio, spy_ret) if r is not None and s is not None]
            if valid:
                xs, ys = zip(*valid)
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=xs, y=ys, mode="markers", name="Monthly", marker=dict(size=5, opacity=0.6)))
                fig.update_layout(title="VIX1M/3M Ratio vs SPY Monthly Returns", xaxis_title="VIX1M/3M Ratio", yaxis_title="SPY Monthly Return (%)", height=500)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Monthly data not available.")

# ---------- Lead-Lag ----------
elif selected_section == "Lead-Lag Analysis":
    st.header("⏱️ Step 3: Lead-Lag Analysis")
    if study != "p03" or not analysis_data or not analysis_data.get("lead_lag"):
        if study == "p02":
            st.info("Lead-lag analysis is available for the HY-IG Spread vs SPY study. Select that study in the sidebar or run analysis for VIX to enable here.")
        else:
            st.warning("Lead-lag data not available. Run analysis.py for Project 03.")
    else:
        ll = analysis_data["lead_lag"]
        best_lag = ll.get("best_lag", "N/A")
        best_corr = ll.get("best_correlation", ll.get("max_correlation"))
        st.write(f"**Best Lag:** {best_lag} month(s)")
        st.write(f"**Best Correlation at Optimal Lag:** {best_corr:.4f}" if isinstance(best_corr, (int, float)) else f"**Max Correlation:** {best_corr}")
        interp = "leads" if (isinstance(best_lag, (int, float)) and best_lag > 0) else ("lags" if isinstance(best_lag, (int, float)) and best_lag < 0 else "is contemporaneous with")
        lags_abs = abs(int(best_lag)) if isinstance(best_lag, (int, float)) else 0
        st.write(f"**Interpretation:** The HY-IG spread {interp} SPY returns by {lags_abs} month(s).")

# ---------- Causality ----------
elif selected_section == "Causality Testing":
    st.header("🔬 Step 4: Causality Testing (Granger Causality)")
    if study == "p02":
        st.info("Causality testing is available for the HY-IG Spread vs SPY study. Select that study to view.")
    else:
        st.write("Granger causality tests whether the indicator helps predict SPY returns beyond past SPY returns.")
        if analysis_data and analysis_data.get("lead_lag"):
            st.write(f"**Optimal Lag (from lead-lag):** {analysis_data['lead_lag'].get('best_lag', 'N/A')} month(s)")
        st.caption("Detailed causality results require running the full analysis script.")

# ---------- Predictive Modeling ----------
elif selected_section == "Predictive Modeling":
    st.header("🤖 Step 5: Predictive Modeling")
    if study == "p02":
        st.info("Predictive modeling is available for the HY-IG Spread vs SPY study. Select that study to view.")
    elif analysis_data and analysis_data.get("predictive_modeling"):
        pm = analysis_data["predictive_modeling"]
        st.write(f"**Mean R²:** {pm.get('mean_r2', pm.get('r2_score', 'N/A')):.4f}" if isinstance(pm.get('mean_r2', pm.get('r2_score')), (int, float)) else "N/A")
        if pm.get("top_features"):
            st.write("**Top features:** " + ", ".join(pm["top_features"]))
        interp = pm.get("mean_r2", 0)
        if isinstance(interp, (int, float)) and interp < 0:
            st.caption("Negative R² indicates the model performs worse than a simple mean predictor; the relationship may require non-linear or regime-specific approaches.")
    else:
        st.warning("Predictive modeling data not available. Run analysis.py for Project 03.")

# ---------- Regime Analysis ----------
elif selected_section == "Regime Analysis":
    st.header("📊 Step 6: Regime Analysis")

    if study == "p03":
        if monthly_data and monthly_data.get("monthly"):
            dates = pd.to_datetime(monthly_data["monthly"]["dates"])
            spreads = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["hy_ig_spread"]]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=spreads, mode="lines", name="HY-IG Spread", line=dict(color="#667eea")))
            fig.update_layout(title="HY-IG Spread Over Time", xaxis_title="Date", yaxis_title="Spread (bps)", height=500)
            st.plotly_chart(fig, use_container_width=True)
        if strategy_data and strategy_data.get("performance_metrics", {}).get("regime_stats"):
            regime_stats = strategy_data["performance_metrics"]["regime_stats"]
            regimes, strat_ret, spy_ret = [], [], []
            for reg, stats in regime_stats.items():
                regimes.append(reg)
                strat_ret.append(stats.get("('Strategy_Return', 'mean')", 0))
                spy_ret.append(stats.get("('SPY_Returns', 'mean')", 0))
            fig = go.Figure()
            fig.add_trace(go.Bar(x=regimes, y=strat_ret, name="Strategy Return", marker_color="#667eea"))
            fig.add_trace(go.Bar(x=regimes, y=spy_ret, name="SPY Return", marker_color="#28a745"))
            fig.update_layout(title="Average Monthly Returns by Regime", xaxis_title="Regime", yaxis_title="Return (%)", height=400, barmode="group")
            st.plotly_chart(fig, use_container_width=True)
    else:
        if monthly_data and monthly_data.get("monthly"):
            dates = pd.to_datetime(monthly_data["monthly"]["dates"])
            ratio = [float(v) if v not in ("null", None) else None for v in monthly_data["monthly"]["ratio"]]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=ratio, mode="lines", name="VIX1M/3M Ratio", line=dict(color="#667eea")))
            fig.update_layout(title="VIX1M/3M Ratio Over Time", xaxis_title="Date", yaxis_title="Ratio", height=500)
            st.plotly_chart(fig, use_container_width=True)
        st.caption("Regime performance (strategy vs SPY by regime) is available for the HY-IG Spread vs SPY study.")

# ---------- Investment Strategy ----------
elif selected_section == "Investment Strategy":
    st.header("💰 Investment Strategy: Backtested Implementation")

    if study == "p02":
        st.info("Investment strategy (backtest, performance metrics, drawdowns) is available for the **HY-IG Spread vs SPY** study. Select that study in the sidebar to view.")
        st.stop()

    if not strategy_data:
        st.warning("Strategy data not available. Please run strategy_backtest.py first.")
        st.stop()

    metrics = strategy_data.get("performance_metrics", {})
    data = strategy_data.get("monthly_data")

    st.subheader("Strategy Framework")
    st.markdown("""
    **Rolling Window Approach:** The strategy uses a **rolling 60-month (5-year) window** to calculate percentile thresholds for HY-IG spread classification.
    - Position size: **100% SPY** (≤P25), **75%** (P25–P50), **50%** (P50–P75), **25%** (P75–P90), **10%** (>P90).
    """)

    st.subheader("Strategy Framework Table")
    if monthly_data and monthly_data.get("stats"):
        s = monthly_data["stats"]
        framework_df = pd.DataFrame([
            {"Spread Regime": "Low Spread (Buy)", "Percentile Range": "≤ 25th", "Current Range (bps)": f"≤ {s['spread_p25']:.2f}", "Position Size": "100% SPY", "Rationale": "Favorable credit conditions"},
            {"Spread Regime": "Moderate-Low", "Percentile Range": "25th–50th", "Current Range (bps)": f"{s['spread_p25']:.2f}–{s['spread_p50']:.2f}", "Position Size": "75% SPY", "Rationale": "Moderate risk"},
            {"Spread Regime": "Moderate-High", "Percentile Range": "50th–75th", "Current Range (bps)": f"{s['spread_p50']:.2f}–{s['spread_p75']:.2f}", "Position Size": "50% SPY", "Rationale": "Elevated risk"},
            {"Spread Regime": "High Spread (Caution)", "Percentile Range": "75th–90th", "Current Range (bps)": f"{s['spread_p75']:.2f}–{s['spread_p90']:.2f}", "Position Size": "25% SPY", "Rationale": "High credit stress"},
            {"Spread Regime": "Very High Spread (Reduce)", "Percentile Range": "> 90th", "Current Range (bps)": f"> {s['spread_p90']:.2f}", "Position Size": "10% SPY", "Rationale": "Severe stress"},
        ])
        st.dataframe(framework_df, use_container_width=True, hide_index=True)

    st.subheader("Performance Metrics")
    if metrics.get("spy") and metrics.get("strategy") and metrics.get("outperformance"):
        perf_df = pd.DataFrame([
            {"Metric": "Total Return", "SPY": f"{metrics['spy']['total_return']:.2f}%", "Strategy": f"{metrics['strategy']['total_return']:.2f}%", "Outperformance": f"{metrics['outperformance']['total_return']:.2f}%"},
            {"Metric": "Annualized Return", "SPY": f"{metrics['spy']['annualized_return']:.2f}%", "Strategy": f"{metrics['strategy']['annualized_return']:.2f}%", "Outperformance": f"{metrics['outperformance']['annualized_return']:.2f}%"},
            {"Metric": "Sharpe Ratio", "SPY": f"{metrics['spy']['sharpe_ratio']:.2f}", "Strategy": f"{metrics['strategy']['sharpe_ratio']:.2f}", "Outperformance": f"+{metrics['outperformance']['sharpe_improvement']:.2f}"},
            {"Metric": "Max Drawdown", "SPY": f"{metrics['spy']['max_drawdown']:.2f}%", "Strategy": f"{metrics['strategy']['max_drawdown']:.2f}%", "Outperformance": f"{metrics['outperformance']['max_dd_improvement']:.2f}% improvement"},
        ])
        st.dataframe(perf_df, use_container_width=True, hide_index=True)

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

        st.subheader("Cumulative Returns Comparison")
        cum_spy = data.get("spy_cumulative") or data.get("cumulative_spy")
        cum_strat = data.get("strategy_cumulative") or data.get("cumulative_strategy")
        if cum_spy and cum_strat:
            cum_spy = [float(v) if v not in ("null", None) else None for v in cum_spy]
            cum_strat = [float(v) if v not in ("null", None) else None for v in cum_strat]
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=dates, y=cum_spy, name="SPY Buy & Hold", line=dict(color="#667eea", width=2)))
            fig.add_trace(go.Scatter(x=dates, y=cum_strat, name="Strategy", line=dict(color="#28a745", width=2)))
            fig.update_layout(height=600, title="Cumulative Returns: Strategy vs Buy & Hold", xaxis_title="Date", yaxis_title="Cumulative Return (multiple)")
            st.plotly_chart(fig, use_container_width=True)

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

    if strategy_data.get("current_strategy_review"):
        st.subheader("Current Strategy Review (Past 1 Year)")
        review = strategy_data["current_strategy_review"]
        if isinstance(review, list) and review:
            review_df = pd.DataFrame(review)
            cols = [c for c in ["date", "regime", "spread", "position_size", "action"] if c in review_df.columns]
            if cols:
                st.dataframe(review_df[cols].head(12), use_container_width=True, hide_index=True)

    if metrics.get("fed_rate_periods"):
        st.subheader("FRED Funds Rate Impact Analysis")
        fed_metrics = metrics["fed_rate_periods"]
        period_labels = {"increase": "Rate Increase", "decrease": "Rate Decrease", "none": "No Change", "rate_above_2.5": "Rate ≥ 2.5%", "rate_below_2.5": "Rate < 2.5%"}
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
                    "Strategy Max DD": f"{m['strategy']['max_drawdown']:.2f}%",
                })
        if rows:
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)

# Footer
st.markdown("---")
if study == "p03":
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 1rem;">
            <p>HY-IG Spread vs SPY | Data: FRED (BAMLH0A0HYM2, BAMLC0A0CM) & Yahoo Finance (SPY) | Generated: {}</p>
        </div>
    """.format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)
else:
    st.markdown("""
        <div style="text-align: center; color: #666; padding: 1rem;">
            <p>VIX1M/3M vs SPY | Data: CBOE VIX & Yahoo Finance (SPY) | Generated: {}</p>
        </div>
    """.format(datetime.now().strftime("%Y-%m-%d")), unsafe_allow_html=True)
