"""
AIG Consolidated Dashboard: Indicator vs ETF Studies (Step C)
Projects: VIX1M/3M vs SPY (Project02), HY-IG Spread vs SPY (Project03)
Deploy to Streamlit Cloud: https://streamlit.io/cloud
"""
import streamlit as st
import json
import numpy as np
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

# Strategy Sandbox — User Guidance Layer (plain language, theory, hypothesis, risk)
SANDBOX_E1_GUIDANCE = {
    "Raw Level": {"description": "Use the original indicator value without modification.", "theory": "Assumes absolute level contains decision-relevant information.", "hypothesis": "Is the indicator level itself sufficient to signal regime change?", "risk": "Sensitive to scale and structural breaks."},
    "Z-score": {"description": "Standardizes indicator relative to its historical mean and volatility.", "theory": "Extreme deviations from historical average may signal stress or opportunity.", "hypothesis": "Does deviation from normal level predict abnormal ETF performance?", "risk": "May overreact in volatile periods."},
    "Percentile Rank": {"description": "Ranks indicator relative to historical distribution.", "theory": "Markets may respond differently when indicator is in extreme tail.", "hypothesis": "Does extreme percentile regime produce different return distribution?", "risk": "Small tail sample size."},
    "Momentum 1M": {"description": "Measures direction and speed of indicator change over 1 month.", "theory": "Trend in indicator may matter more than level.", "hypothesis": "Does accelerating change precede ETF adjustment?", "risk": "Whipsaw in noisy periods."},
    "Momentum 3M": {"description": "Measures direction and speed of indicator change over 3 months.", "theory": "Trend in indicator may matter more than level.", "hypothesis": "Does accelerating change precede ETF adjustment?", "risk": "Whipsaw in noisy periods."},
    "Momentum 6M": {"description": "Measures direction and speed of indicator change over 6 months.", "theory": "Trend in indicator may matter more than level.", "hypothesis": "Does accelerating change precede ETF adjustment?", "risk": "Whipsaw in noisy periods."},
    "Rate of Change": {"description": "Percentage change in indicator from prior period.", "theory": "Rate of change can signal momentum or reversal earlier than level.", "hypothesis": "Does rate of change in indicator lead ETF returns?", "risk": "Noisy when indicator is near zero or in low-volatility regimes."},
}
SANDBOX_E2_GUIDANCE = {
    "Above X percentile": {"meaning": "Indicator is in the top (100−X)% of historical range.", "interpretation": "Extreme regime condition (e.g. stress or exuberance).", "tested_behaviour": "How ETF performs during high-percentile regimes.", "risk": "Sensitive to choice of X; small sample in tail."},
    "Below X percentile": {"meaning": "Indicator is in the bottom X% of historical range.", "interpretation": "Low or compressed regime.", "tested_behaviour": "How ETF performs when indicator is in lower tail.", "risk": "Sensitive to choice of X; small sample in tail."},
    "Cross Median": {"meaning": "Indicator crosses long-term central tendency.", "interpretation": "Regime shift signal.", "tested_behaviour": "Transition effect on ETF returns.", "risk": "Can trigger frequently in sideways markets."},
    "Z-score > +1": {"meaning": "Indicator is more than one standard deviation above its rolling mean.", "interpretation": "Unusually high / stress regime.", "tested_behaviour": "ETF performance when indicator is extended above normal.", "risk": "Requires Z-score transformation to be meaningful."},
    "Z-score < -1": {"meaning": "Indicator is more than one standard deviation below its rolling mean.", "interpretation": "Unusually low / compressed regime.", "tested_behaviour": "ETF performance when indicator is extended below normal.", "risk": "Requires Z-score transformation to be meaningful."},
    "Momentum > 0": {"meaning": "Indicator is rising (positive change over lookback).", "interpretation": "Upside momentum in the indicator.", "tested_behaviour": "Whether positive indicator momentum precedes ETF adjustment.", "risk": "Lagging; can whipsaw at turning points."},
}
SANDBOX_E3_GUIDANCE = {
    "Long Only (In/Out)": {"meaning": "Invest fully only when signal is active; otherwise no exposure.", "use_case": "Binary tactical exposure.", "risk": "Full drawdown when in market; no partial hedging."},
    "Risk Reduction (50% exposure)": {"meaning": "Reduce exposure (e.g. to 50%) when condition is met, rather than full exit.", "use_case": "Risk overlay, not pure timing.", "risk": "Still exposed during stress; mitigates but does not eliminate."},
    "Full Defensive (0% exposure)": {"meaning": "Fully exit market when condition is active.", "use_case": "Stress avoidance.", "risk": "Miss upside if condition is persistent; opportunity cost."},
}


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

# Sidebar: Home + section list (Strategy Sandbox = Layer 2, independent section)
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
        "Strategy Sandbox",
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

# ---------- Strategy Sandbox (Layer 2 — independent section) ----------
elif selected_section == "Strategy Sandbox":
    st.header("🧪 Strategy Sandbox")
    st.caption("Configure transformation, threshold, and position logic. Uses Tier1 indicator and ETF returns only (no new data fetch).")

    # Build Tier1 from existing monthly_data only
    def _tier1_from_monthly(monthly_data, study_id):
        if not monthly_data or not monthly_data.get("monthly"):
            return None, None
        m = monthly_data["monthly"]
        dates = pd.to_datetime(m["dates"])
        if study_id == "p03":
            ind = [float(x) if x not in ("null", None) else np.nan for x in m["hy_ig_spread"]]
            ret = [float(x) if x not in ("null", None) else np.nan for x in m["spy_returns"]]
        else:
            ind = [float(x) if x not in ("null", None) else np.nan for x in m.get("ratio", [])]
            spy_prices = [float(x) if x not in ("null", None) else np.nan for x in m.get("spy", [])]
            ret = compute_spy_returns_from_prices(spy_prices)
            if len(ret) != len(dates):
                ret = (ret + [None] * len(dates))[:len(dates)]
        df = pd.DataFrame({"indicator": ind, "etf_return": ret}, index=dates).dropna(how="all")
        df = df.dropna(subset=["indicator", "etf_return"])
        if df.empty or len(df) < 12:
            return None, None
        return df["indicator"], df["etf_return"]

    indicator_series, etf_return_series = _tier1_from_monthly(monthly_data, study)
    if indicator_series is None or etf_return_series is None:
        st.warning("Tier1 data not available for Sandbox. Ensure monthly data exists and has indicator + ETF returns.")
        st.stop()

    date_min_avail = indicator_series.index.min()
    date_max_avail = indicator_series.index.max()

    # Top Panel — Strategy Configuration
    with st.expander("Strategy Configuration", expanded=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            transformation = st.selectbox(
                "Transformation",
                ["Raw Level", "Z-score", "Percentile Rank", "Momentum 1M", "Momentum 3M", "Momentum 6M", "Rate of Change"],
                index=0,
                key="sandbox_transform",
            )
            with st.expander("What does this mean? — Transformation (i)", expanded=False):
                g1 = SANDBOX_E1_GUIDANCE.get(transformation, {})
                if g1:
                    st.markdown("**Description**  \n" + g1.get("description", ""))
                    st.markdown("**Theory**  \n" + g1.get("theory", ""))
                    st.markdown("**Hypothesis being tested**  \n" + g1.get("hypothesis", ""))
                    st.markdown("**Risk**  \n" + g1.get("risk", ""))
            z_window = 60
            if transformation == "Z-score":
                z_window = st.number_input("Z-score rolling window", min_value=12, max_value=120, value=60, step=6, key="sandbox_z")
        with c2:
            threshold_rule = st.selectbox(
                "Threshold",
                ["Above X percentile", "Below X percentile", "Cross Median", "Z-score > +1", "Z-score < -1", "Momentum > 0"],
                index=0,
                key="sandbox_thresh",
            )
            with st.expander("What does this mean? — Threshold (i)", expanded=False):
                g2 = SANDBOX_E2_GUIDANCE.get(threshold_rule, {})
                if g2:
                    st.markdown("**Meaning**  \n" + g2.get("meaning", ""))
                    st.markdown("**Interpretation**  \n" + g2.get("interpretation", ""))
                    st.markdown("**Tested behaviour**  \n" + g2.get("tested_behaviour", ""))
                    st.markdown("**Risk**  \n" + g2.get("risk", ""))
            above_pct = 70.0
            below_pct = 30.0
            if threshold_rule == "Above X percentile":
                above_pct = st.slider("Percentile (above)", 50, 95, 70, key="sandbox_above")
            elif threshold_rule == "Below X percentile":
                below_pct = st.slider("Percentile (below)", 5, 50, 30, key="sandbox_below")
        with c3:
            position_mode = st.selectbox(
                "Position Logic",
                ["Long Only (In/Out)", "Risk Reduction (50% exposure)", "Full Defensive (0% exposure)"],
                index=0,
                key="sandbox_pos",
            )
            with st.expander("What does this mean? — Position (i)", expanded=False):
                g3 = SANDBOX_E3_GUIDANCE.get(position_mode, {})
                if g3:
                    st.markdown("**Meaning**  \n" + g3.get("meaning", ""))
                    st.markdown("**Use case**  \n" + g3.get("use_case", ""))
                    st.markdown("**Risk**  \n" + g3.get("risk", ""))
        # Dynamic line: what the user is currently testing
        _thresh_short = {"Above X percentile": "extreme high regime", "Below X percentile": "extreme low regime", "Cross Median": "regime shift", "Z-score > +1": "extended high regime", "Z-score < -1": "extended low regime", "Momentum > 0": "positive momentum"}
        _pos_short = {"Long Only (In/Out)": "tactical exposure", "Risk Reduction (50% exposure)": "risk overlay", "Full Defensive (0% exposure)": "stress avoidance"}
        _trans_short = {"Raw Level": "indicator level", "Z-score": "indicator deviation", "Percentile Rank": "indicator percentile", "Momentum 1M": "1M momentum", "Momentum 3M": "3M momentum", "Momentum 6M": "6M momentum", "Rate of Change": "rate of change"}
        testing_line = "**You are currently testing:** Indicator {} impact on ETF {} ({}).".format(
            _trans_short.get(transformation, transformation.lower()),
            _pos_short.get(position_mode, position_mode.lower()),
            _thresh_short.get(threshold_rule, threshold_rule.lower()),
        )
        st.info(testing_line)
        d_min = date_min_avail.date() if hasattr(date_min_avail, "date") else date_min_avail
        d_max = date_max_avail.date() if hasattr(date_max_avail, "date") else date_max_avail
        col_d1, col_d2 = st.columns(2)
        with col_d1:
            date_start = st.date_input("Start date", value=d_min, min_value=d_min, max_value=d_max, key="sandbox_start")
        with col_d2:
            date_end = st.date_input("End date", value=d_max, min_value=d_min, max_value=d_max, key="sandbox_end")
        dr_min = pd.Timestamp(date_start)
        dr_max = pd.Timestamp(date_end)
        if dr_min > dr_max:
            dr_min, dr_max = dr_max, dr_min

        run_clicked = st.button("Run Sandbox Strategy", type="primary", key="sandbox_run")

    result = None
    if run_clicked:
        try:
            from sandbox_engine import run_sandbox
        except ImportError:
            from Project03.sandbox_engine import run_sandbox
        res = run_sandbox(
            indicator_series,
            etf_return_series,
            transformation=transformation,
            threshold_rule=threshold_rule,
            position_mode=position_mode,
            above_pct=above_pct,
            below_pct=below_pct,
            z_window=z_window,
            date_min=dr_min,
            date_max=dr_max,
        )
        if res.get("error"):
            st.error(res["error"])
            result = res
        else:
            st.session_state["sandbox_result"] = res
            st.rerun()
    else:
        result = st.session_state.get("sandbox_result")

    if result and not result.get("error"):
        # Sample size warning (Guardrail 3)
        if result.get("sample_size_warning"):
            st.warning("⚠ Strategy sample size may be insufficient for statistical reliability (Number of Trades < 5 or Active Periods < 5% of dataset).")

        # Middle Panel — Performance Summary (Strategy | Benchmark)
        st.subheader("Performance Summary")
        left, right = st.columns(2)
        met = result["evaluation_metrics"]
        with left:
            st.markdown("**Strategy Metrics**")
            s = met["strategy"]
            st.metric("Total Return", f"{s['total_return']:.2f}%")
            st.metric("CAGR", f"{s['cagr']:.2f}%")
            st.metric("Sharpe Ratio", f"{s['sharpe_ratio']:.2f}")
            st.metric("Max Drawdown", f"{s['max_drawdown']:.2f}%")
            st.metric("Volatility", f"{s['volatility']:.2f}%")
            st.metric("Win Rate", f"{s['win_rate']:.1f}%")
            st.metric("Calmar Ratio", f"{s['calmar_ratio']:.2f}")
        with right:
            st.markdown("**Benchmark (ETF Buy & Hold)**")
            b = met["benchmark"]
            st.metric("Total Return", f"{b['total_return']:.2f}%")
            st.metric("CAGR", f"{b['cagr']:.2f}%")
            st.metric("Sharpe Ratio", f"{b['sharpe_ratio']:.2f}")
            st.metric("Max Drawdown", f"{b['max_drawdown']:.2f}%")
            st.metric("Volatility", f"{b['volatility']:.2f}%")
            st.metric("Win Rate", f"{b['win_rate']:.1f}%")
            st.metric("Calmar Ratio", f"{b['calmar_ratio']:.2f}")

        # Sample size metrics
        st.subheader("Sample Size Metrics")
        ss = result["sample_size_metrics"]
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.metric("Number of Trades", ss["n_trades"])
            st.metric("Active Periods", ss["n_active_periods"])
        with sc2:
            st.metric("Avg Holding Period", f"{ss['avg_holding_period']:.1f} periods")
            st.metric("% Time in Market", f"{ss['pct_time_in_market']:.1f}%")
        with sc3:
            st.metric("Max Holding Period", ss["max_holding_period"])
        with sc4:
            st.metric("Min Holding Period", ss["min_holding_period"])

        # Bottom Panel — Visual Output
        st.subheader("Charts")
        dates = result["dates"]
        cum_s = result["strategy_cumulative"].values
        cum_b = result["benchmark_cumulative"].values
        dd_s = result["strategy_drawdown"].values
        dd_b = result["benchmark_drawdown"].values
        exp = result["exposure"].values

        fig_equity = go.Figure()
        fig_equity.add_trace(go.Scatter(x=dates, y=cum_s, name="Strategy", line=dict(color="#28a745", width=2)))
        fig_equity.add_trace(go.Scatter(x=dates, y=cum_b, name="Benchmark (ETF Buy & Hold)", line=dict(color="#667eea", width=2)))
        fig_equity.update_layout(title="Equity Curve: Strategy vs Benchmark", xaxis_title="Date", yaxis_title="Cumulative Return (multiple)", height=400)
        st.plotly_chart(fig_equity, use_container_width=True)

        fig_dd = go.Figure()
        fig_dd.add_trace(go.Scatter(x=dates, y=dd_s, name="Strategy Drawdown", fill="tozeroy", line=dict(color="#28a745")))
        fig_dd.add_trace(go.Scatter(x=dates, y=dd_b, name="Benchmark Drawdown", fill="tozeroy", line=dict(color="#667eea")))
        fig_dd.update_layout(title="Drawdown Comparison", xaxis_title="Date", yaxis_title="Drawdown (%)", height=350)
        st.plotly_chart(fig_dd, use_container_width=True)

        fig_exp = go.Figure()
        fig_exp.add_trace(go.Scatter(x=dates, y=exp, name="Exposure", line=dict(color="#6c757d"), fill="tozeroy"))
        fig_exp.update_layout(title="Exposure Timeline", xaxis_title="Date", yaxis_title="Exposure (0–1)", height=300)
        st.plotly_chart(fig_exp, use_container_width=True)

        # Download config + metrics as CSV
        st.subheader("Export")
        config = result.get("config", {})
        rows = [{"metric": "Strategy Total Return %", "value": met["strategy"]["total_return"]}, {"metric": "Strategy CAGR %", "value": met["strategy"]["cagr"]}, {"metric": "Strategy Sharpe", "value": met["strategy"]["sharpe_ratio"]}, {"metric": "Strategy Max DD %", "value": met["strategy"]["max_drawdown"]}, {"metric": "Benchmark Total Return %", "value": met["benchmark"]["total_return"]}, {"metric": "Benchmark CAGR %", "value": met["benchmark"]["cagr"]}]
        for k, v in config.items():
            rows.append({"metric": f"config_{k}", "value": v})
        for k, v in ss.items():
            rows.append({"metric": f"sample_{k}", "value": v})
        export_df = pd.DataFrame(rows)
        st.download_button(
            "Download configuration + metrics (CSV)",
            data=export_df.to_csv(index=False).encode("utf-8"),
            file_name=f"sandbox_config_metrics_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv",
            key="sandbox_download",
        )
    elif result and result.get("error"):
        st.error(result["error"])

    # ---------- Strategy Ranking Panel (add-on; informational only) ----------
    st.divider()
    st.subheader("🔍 Strategy Ranking Panel")
    st.caption("Top 10 strategy combinations from predefined grid (75 combinations). Excluded by guardrail: Trades < 5 or % Time in Market < 5%.")
    if st.button("Compute Top 10", key="sandbox_ranking_run"):
        try:
            from sandbox_engine import run_ranking_grid
        except ImportError:
            from Project03.sandbox_engine import run_ranking_grid
        with st.spinner("Running 75 combinations…"):
            top10, n_excluded = run_ranking_grid(
                indicator_series,
                etf_return_series,
                date_min=date_min_avail,
                date_max=date_max_avail,
                z_window=60,
            )
        st.session_state["sandbox_ranking"] = {"top10": top10, "n_excluded": n_excluded}
        st.rerun()
    ranking = st.session_state.get("sandbox_ranking")
    if ranking:
        top10 = ranking["top10"]
        n_excluded = ranking["n_excluded"]
        if n_excluded > 0:
            st.caption(f"Combinations excluded by guardrail (Trades < 5 or Time in Market < 5%): {n_excluded}.")
        if top10:
            rank_df = pd.DataFrame(top10)
            st.dataframe(rank_df, use_container_width=True, hide_index=True)
        else:
            st.info("No combinations passed the guardrail (all had Trades < 5 or % Time in Market < 5%). Try a different date range or indicator.")
    else:
        st.info("Click **Compute Top 10** to run the predefined grid (Raw, Z-score, Percentile, Momentum 1M/3M × Top 80%, Bottom 20%, Cross Median, Z>+1, Z<-1 × Long Only, Risk Reduction, Defensive).")

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
