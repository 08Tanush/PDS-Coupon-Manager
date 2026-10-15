# PDS Coupon Manager — local Python dashboard

This adds a **local-only Flask/Jinja2 dashboard** to the existing coupon generator. No React, Node.js, or custom frontend JavaScript. It is **not yet a Shopify embedded Admin app** and must **not** be deployed publicly without implementing Shopify embedded authentication, authorization, session handling, HTTPS and deployment hardening.

## Start on your Windows PC

```powershell
cd PDS-Coupon-Manager-Hospital
python -m pip install -r requirements.txt
```

Keep your existing `.env` Shopify credentials. Add two new, independently generated long random secrets to `.env`:

```
PDS_ADMIN_PASSWORD=replace_with_long_random_password
PDS_SESSION_SECRET=replace_with_independent_long_random_secret
```

Generate values locally with `python -c "import secrets; print(secrets.token_urlsafe(40))"` twice. Do not share `.env` or credentials.

```powershell
python -m unittest discover -s tests -v
python web_app.py
```

Open **http://127.0.0.1:5000** and sign in using `PDS_ADMIN_PASSWORD`.

## Safety and behavior

- The dashboard is deliberately bound to `127.0.0.1` and is not an embedded Shopify app.
- The Generate button **creates live Shopify discounts** only after the explicit checkbox confirmation. It does not run a dry run first.
- Each batch uses a unique SQLite journal in `output/`, avoiding overwriting earlier batches.
- Shopify bulk import can be asynchronous. Review each batch and use **Resume / check imports** for incomplete jobs.
- The verified CSV exports only `CREATED` codes. The audit CSV includes all statuses and error messages.
- **Single-use redemption per individual code has not been proven.** Do not distribute patient coupons until verified.
- Existing CLI `main.py` remains available and unchanged.
- Existing CLI-created journals are preserved but not included in the dashboard's batch list, which lists `batch_*.sqlite3`.
- Hospital discount categories have not been introduced.
- The original Shopify API behavior and retry/recovery limitations remain; production operations need controlled testing.

## Future embedded Shopify app

Shopify Dev Dashboard still points to `https://example.com` and `embedded=false`. Keep those settings unchanged. An embedded version will require public HTTPS hosting, proper Shopify authentication/session tokens, and some browser-side Shopify App Bridge JavaScript even though the business logic can remain Python. The local password is not a substitute for Shopify Admin identity.
