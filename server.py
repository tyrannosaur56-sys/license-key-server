import os
import logging
from flask import Flask, jsonify, request
import stripe

# ====== Config ======
stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ.get("STRIPE_WEBHOOK_SECRET", "")
DOMAIN = os.getenv("DOMAIN", "").rstrip("/")  # optional; leave blank to use Stripe's default success page

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# ====== Health ======
@app.route("/", methods=["GET", "HEAD", "OPTIONS"])
def health():
    return jsonify({"status": "ok"}), 200

# ====== Product catalog (live prices) ======
@app.route("/product-catalog", methods=["GET", "HEAD", "OPTIONS"])
def product_catalog():
    prices = stripe.Price.list(active=True, expand=["data.product"]).data
    catalog = []
    for price in prices:
        prod = price.product
        catalog.append({
            "price_id": price.id,
            "unit_amount": price.unit_amount,
            "currency": price.currency,
            "product": {
                "id": prod.id,
                "name": prod.name,
                "description": prod.description,
            },
        })
    return jsonify(catalog), 200

# ====== Create Checkout Session ======
@app.route("/create-checkout-session", methods=["POST", "OPTIONS"])
def create_checkout_session():
    """
    Body (JSON):
      { "price_id": "price_xxx", "quantity": 1 }
    """
    data = request.get_json(force=True) if request.data else {}
    price_id = data.get("price_id") or data.get("priceId")  # support both keys
    quantity = int(data.get("quantity", 1))

    if not price_id:
        return jsonify({"error": "price_id is required"}), 400

    # Detect subscription vs one-time from the Price object
    price_obj = stripe.Price.retrieve(price_id)
    mode = "subscription" if getattr(price_obj, "recurring", None) else "payment"

    success_url = f"{DOMAIN}/success?session_id={{CHECKOUT_SESSION_ID}}" if DOMAIN else None
    cancel_url = f"{DOMAIN}/cancel" if DOMAIN else None

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": quantity}],
            mode=mode,
            # If you didn't set DOMAIN, Stripe's own "return to your site" will show;
            # providing at least success_url is recommended for real flows.
            **({ "success_url": success_url } if success_url else {}),
            **({ "cancel_url": cancel_url } if cancel_url else {}),
        )
        return jsonify({"url": session.url}), 200
    except stripe.error.InvalidRequestError as e:
        app.logger.error(f"Stripe InvalidRequest: {e.user_message or str(e)}")
        return jsonify({"error": e.user_message or "Stripe invalid request"}), 400
    except Exception as e:
        app.logger.exception("Create checkout session failed")
        return jsonify({"error": "Server error creating checkout"}), 500

# ====== Webhook ======
@app.route("/webhook", methods=["POST", "OPTIONS"])
def webhook():
    payload = request.data
    sig = request.headers.get("Stripe-Signature", "")

    if not WEBHOOK_SECRET:
        app.logger.warning("No STRIPE_WEBHOOK_SECRET set; rejecting to avoid spoofing.")
        return jsonify({"error": "Webhook secret not configured"}), 500

    try:
        event = stripe.Webhook.construct_event(payload=payload, sig_header=sig, secret=WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400
    except Exception:
        return "Invalid payload", 400

    etype = event["type"]
    app.logger.info(f"▶ Received event: {etype}")

    # Minimal handlers; expand as needed
    if etype == "checkout.session.completed":
        # You can fetch and fulfill here
        app.logger.info("checkout.session.completed handled")
    elif etype == "invoice.payment_succeeded":
        app.logger.info("invoice.payment_succeeded handled")
    elif etype in ("customer.subscription.deleted", "invoice.payment_failed"):
        app.logger.info(f"{etype} handled")

    return "", 200

# ====== Log routes on startup ======
for rule in app.url_map.iter_rules():
    app.logger.info(f"Route: {rule} → methods={sorted(list(rule.methods))}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

