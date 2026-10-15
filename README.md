# PDS Hospital Coupon Manager — grouped native Shopify discounts

**Status: Implementation candidate; not live Shopify verified.** No Shopify store or discount was modified when building this ZIP.

## What it does

- Enter a hospital name, optionally override its abbreviation, choose 50 / 100 / 500 / custom coupon count.
- Each coupon independently receives a secure random choice of **6%, 7%, or 8%**. No fixed sequence or quota.
- One native Shopify parent discount **per percentage present** (at most three per batch). Each parent holds the matching redeem codes. These are *not literal folders* in Shopify Admin.
- Each parent has `usageLimit: 1` as requested, but **per-code versus per-discount usage semantics must be verified with a real checkout test** before issuing hundreds. If the limit is discount-wide, this grouped model is **not suitable** for single-use-per-code requirements without a different Shopify discount implementation.
- Durable SQLite journal, read-only resume preview, asynchronous Shopify bulk-import job checks, and export of only Shopify-confirmed codes.
- No government/private category. No virtual environment or third-party Python dependencies.

## Run (PowerShell)

```powershell
Copy-Item .env.example .env
notepad .env
python -m unittest discover -s tests -v
python test_connection.py
python main.py create --hospital "Tata Memorial Hospital" --count 5
```

Fill `SHOPIFY_CLIENT_ID` and `SHOPIFY_CLIENT_SECRET` in `.env` **locally**. Do not share the file.

**After explicit approval to create real production discounts and controlled test:**

```powershell
python main.py create --hospital "Tata Memorial Hospital" --count 5 --journal output/tata_test.sqlite3 --confirm
```

Resume if interrupted (same journal, never delete it):

```powershell
python main.py resume --journal output/tata_test.sqlite3
python main.py resume --journal output/tata_test.sqlite3 --confirm
```

New batches **must use new journal paths**. A completed batch creates `output/tata_test.csv` and `output/tata_test_audit.csv`.

## Important limitations

1. **This is a CLI implementation, not an embedded Shopify Admin UI.** A Generate button *inside Shopify Admin* requires a separately deployed authenticated embedded app with a public HTTPS URL. The existing non-embedded API app cannot host a UI through this local ZIP alone.
2. **Single-use-per-code behavior is unverified.** `usageLimit: 1` on a parent may have semantics that need checkout verification. Do not hand out codes until two codes from the same parent have been redeemed independently and one used code is rejected on a second purchase.
3. **Asynchronous imports can be ambiguous.** Codes with `SENDING`, `UNKNOWN`, or `FAILED` statuses are not exported as distributable. Manual Shopify reconciliation may be needed; ambiguous submissions are never automatically retried.
4. **The parent discount's seed code is a real coupon**, and is included in the generated count.
5. **No patient ID/login/hospital eligibility/cooldown checks.** Codes are bearer tokens. Shopify checkout displays actual discounts.
6. Existing five individual test discounts are untouched. No automatic deletion or migration.
7. Hospital abbreviations may collide for similarly named hospitals. The generated 16-character random suffix avoids code collisions with overwhelming probability; Shopify also checks uniqueness. Each batch creates separate parent discounts; future hospital-level reuse is not implemented.

### Next production gate

Validate API authentication, run the test suite, create a tiny controlled batch, verify native Shopify Admin grouping, asynchronous imports, **and two same-percentage codes redeem independently**. Only then consider 50/100/500 and a hosted Shopify embedded Admin UI.
