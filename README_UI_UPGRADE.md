# PDS Coupon Manager — Glass Dashboard Upgrade

This release restyles the existing local Flask dashboard with glassmorphism, responsive navigation, gradient hero, coupon form, real SQLite-derived statistics, latest batch distribution donut, and batch history table.

## Start (Windows PowerShell)

1. Extract this ZIP into a NEW directory, not over your working installation.
2. Copy your existing `.env` into the folder containing `web_app.py`. Do not share this file.
3. Copy your existing `output/batch_*.sqlite3` journals and their CSV exports into the new project's `output/` folder if you want the same history. Do not overwrite any batch files.
4. `python -m pip install -r requirements.txt`
5. `python -m unittest discover -s tests -v`
6. `python web_app.py`
7. Open http://127.0.0.1:5000, sign in, and hard-refresh with Ctrl+F5.

## Notes

- Backend coupon generation and GraphQL import routines are unchanged.
- Generating coupons still writes LIVE discounts to your production Shopify store. Explicit approval checkbox is required.
- Single-use redemption is not yet verified.
- Only dashboard-generated journals named `batch_*.sqlite3` appear in the dashboard. Earlier CLI journals remain preserved but are not included in this dashboard's statistics.
- This is a local password-protected dashboard, NOT an embedded Shopify Admin app. Do not expose it publicly as-is.
- Google Fonts are loaded from an external stylesheet; if offline, system fonts are used.
- No React, Node.js, or custom browser JavaScript is required.
