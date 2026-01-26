# Deploy Project03 Dashboard to Streamlit Cloud

This guide will help you deploy your HY-IG Spread Indicator Analysis dashboard to Streamlit Cloud so your teammates can access it online.

## Prerequisites

1. **GitHub Repository**: Your Project03 should be pushed to GitHub (already done: https://github.com/yyycom18/AIG-Step-C-demo)
2. **Streamlit Account**: Sign up at https://streamlit.io/cloud (free tier available)

## Deployment Steps

### 1. Sign in to Streamlit Cloud

1. Go to https://share.streamlit.io/
2. Sign in with your GitHub account
3. Authorize Streamlit to access your GitHub repositories

### 2. Deploy Your App

1. Click **"New app"** button
2. Select your repository: `yyycom18/AIG-Step-C-demo`
3. **Main file path**: Enter `streamlit_app.py`
4. **App URL**: Choose a custom URL (e.g., `hy-ig-spread-analysis`)
5. Click **"Deploy!"**

### 3. Configure Environment Variables (if needed)

If your app needs the FRED API key:

1. Go to your app settings in Streamlit Cloud
2. Click **"Secrets"** tab
3. Add your FRED API key:
   ```toml
   FRED_API_KEY = "your_api_key_here"
   ```

**Note**: For this dashboard, the FRED API key is only needed if you want to refresh data. The app will work with existing data files (`data/hyig_data.json`, `outputs/*.json`).

### 4. Ensure Data Files are in Repository

Make sure these files are committed to your GitHub repo:
- `data/hyig_data.json`
- `outputs/analysis_summary.json`
- `outputs/strategy_backtest.json`

If they're not in the repo:
```bash
git add data/hyig_data.json outputs/*.json
git commit -m "Add data files for Streamlit deployment"
git push
```

Streamlit Cloud will automatically redeploy when you push changes.

## Updating Your Dashboard

1. Make changes to `streamlit_app.py` or data files
2. Commit and push to GitHub:
   ```bash
   git add .
   git commit -m "Update dashboard"
   git push
   ```
3. Streamlit Cloud will automatically redeploy (usually takes 1-2 minutes)

## Access Your Dashboard

Once deployed, your dashboard will be available at:
**https://[your-app-name].streamlit.app**

Share this URL with your teammates!

## Troubleshooting

### App fails to load
- Check that all required files (`data/hyig_data.json`, `outputs/*.json`) are in the repository
- Check the Streamlit Cloud logs for error messages
- Ensure `requirements.txt` includes all dependencies

### Data not showing
- Verify JSON files are valid JSON
- Check file paths in `streamlit_app.py` match your repository structure
- Ensure files are committed to the `main` branch

### Performance issues
- Large data files may slow down loading
- Consider using `@st.cache_data` decorators (already added in the app)

## Local Testing

Before deploying, test locally:

```bash
# Install streamlit
pip install streamlit

# Run the app
streamlit run streamlit_app.py
```

The app will open at `http://localhost:8501`

## Files Structure for Deployment

```
Project03/
├── streamlit_app.py          # Main Streamlit app (REQUIRED)
├── requirements.txt           # Python dependencies (REQUIRED)
├── .streamlit/
│   └── config.toml          # Streamlit configuration (optional)
├── data/
│   └── hyig_data.json        # Monthly data (REQUIRED)
└── outputs/
    ├── analysis_summary.json  # Analysis results (REQUIRED)
    └── strategy_backtest.json # Strategy metrics (REQUIRED)
```

## Next Steps

1. Deploy to Streamlit Cloud using the steps above
2. Share the URL with your teammates
3. Update data periodically by running `fetch_data.py` and `analysis.py` locally, then pushing updated JSON files to GitHub
