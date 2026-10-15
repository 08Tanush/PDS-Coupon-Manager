# Editorial dashboard redesign

Visual direction: Pharmacy Door Step blog — airy lavender/mint background, elegant serif typography, glass cards, no nonfunctional navigation.

Preserved: existing Flask routes, login, CSRF, coupon generation, SQLite batch journals, Shopify grouped discounts, CSV downloads and batch history.

The Generate button writes live discounts to Shopify after explicit confirmation. Single-use redemption has not been verified.

To run: install requirements, copy your own .env from the prior local project, run `python web_app.py`. Do not upload secrets.

Google Fonts is an optional visual enhancement. If unavailable, the interface falls back to Georgia and Arial.
