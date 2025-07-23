
AutoRoster License Key Server (Flask + JSON)
--------------------------------------------

HOW TO USE:
1. Install dependencies:
   pip install flask

2. Set your Stripe webhook secret inside config.json

3. Run the server:
   python server.py

4. Set your Stripe webhook to:
   https://yourdomain.com/webhook  (for live)
   http://localhost:4242/webhook   (for local testing)

This server will:
- Capture email from custom_fields in Stripe Checkout
- Generate license key by tier (Lite / Standard / Pro)
- Save to licenses.json

Make sure Stripe sends metadata (tier) and collects email via custom fields.
