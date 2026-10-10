# GreenPulse — Streamlit app

## Run on Windows
1. Extract the ZIP.
2. Open the `GreenPulse_Fully_Working` folder.
3. Click the File Explorer address bar, type `cmd`, press Enter.
4. Run:

```bat
py -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m streamlit run app.py
```

If `py` is not recognised, replace `py` with `python`.

## Live SerpApi results
Paste your **newly rotated** SerpApi key into the password field in the app sidebar. Or create `.streamlit\secrets.toml` containing:

```toml
SERPAPI_KEY = "PASTE_YOUR_NEW_KEY_HERE"
```

Restart Streamlit after editing secrets. Do not share the key or commit it to GitHub. A previously exposed key should be revoked and replaced in the SerpApi dashboard.

Without a key the app runs in demo/guidance mode and provides direct Google Maps search links; it does not pretend sample businesses are live results.

## Troubleshooting
- Missing modules: activate `.venv`, then run `pip install -r requirements.txt`.
- `HTTP 401/403`: check key and account access.
- `HTTP 429`: check quota/rate limits.
- `HTTP 400`: read the SerpApi error text shown in the app.
