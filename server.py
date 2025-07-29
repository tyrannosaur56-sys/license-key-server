
import os
import logging

from flask import Flask, jsonify, request
import stripe

# ─── Load your Stripe secret key ──────────────────────────────────────────────
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)


@app.route("/", methods=["HEAD", "GET", "OPTIONS"])
def root():
    return jsonify({"status": "ok"})


@app.route("/product-catalog", methods=["HEAD", "GET", "OPTIONS"])
def product_catalog():
    """
    List all active Prices (and their Product metadata) so
    your frontend can render a catalog or pricing table.
    """
    prices = stripe.Price.list(
        active=True,
        expand=["data.product"]
    ).data

    catalog = []
    for price in prices:
        prod = price.product
        catalog.append({
            "price_id": price.id,
            "unit_amount": price.unit_amount,
            "currency": price.currency,
            "product": {
                "id":    prod.id,
                "name":  prod.name,
                "description": prod.description,
            }
        })

    return jsonify(catalog)


@app.route("/create-checkout-session", methods=["POST", "OPTIONS"])
def create_checkout_session():
    """
    Create a Checkout Session for either one-time or subscription
    purchases, depending on the Price’s `recurring` attribute.
    Frontend posts JSON:
      { "priceId": "...", "quantity": 1 }
    """
    data = request.get_json(force=True)
    price_id = data.get("priceId")
    quantity = data.get("quantity", 1)
    domain   = os.getenv("DOMAIN", "").rstrip("/")

    # Retrieve the Price object so we know if it’s a subscription
    price_obj = stripe.Price.retrieve(price_id)
    mode = "subscription" if getattr(price_obj, "recurring", None) else "payment"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        mode=mode,
        line_items=[{"price": price_id, "quantity": quantity}],
        success_url=f"{domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url =f"{domain}/cancel",
    )
    return jsonify({"url": session.url})


@app.route("/webhook", methods=["POST", "OPTIONS"])
def webhook_received():
    """
    A simple catch‐all webhook endpoint.
    Right now signature verification is OFF so curl/raw posts will hit it.
    Later, set STRIPE_WEBHOOK_SECRET and use stripe.Webhook.construct_event().
    """
    payload = request.get_data(as_text=True)
    # If you want signature verification, uncomment below:
    # sig_header = request.headers.get("Stripe-Signature", "")
    # webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
    # try:
    #     event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    # except Exception as e:
    #     return jsonify({"error": str(e)}), 400
    # data = event["data"]["object"]

    # For now just parse JSON and log it
    try:
        event = request.get_json(force=True)
    except Exception:
        return jsonify({"error": "Invalid payload"}), 400

    t = event.get("type")
    logging.info(f"▶ Received event: {t}")
    # Example: if you get `checkout.session.completed`, you can
    # fulfill the order / generate a license key here.

    return jsonify({"status": "received"}), 200


# ─── Log all registered routes ────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO)
for rule in app.url_map.iter_rules():
    logging.info(f"Route: {rule} → methods={list(rule.methods)}")


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
