# Project 02 data for Streamlit Cloud

When the app is deployed on **Streamlit Community Cloud** with Project03 as the app root, the server cannot see the sibling folder `Project02`. To make the **VIX1M/3M vs SPY** study work in the cloud:

1. Copy `vix_data.json` from Project02 into this folder:
   - **From repo root:**  
     `copy Project02\data\vix_data.json Project03\data_p02\` (Windows)  
     or  
     `cp Project02/data/vix_data.json Project03/data_p02/` (Mac/Linux)
2. Commit and push so that `Project03/data_p02/vix_data.json` is in the repo.
3. Redeploy the app on Streamlit Cloud.

To generate or refresh the file locally, run in the Project02 folder:

```bash
cd Project02
python fetch_vix_data.py
```

Then copy the new `data/vix_data.json` into this folder as above.
