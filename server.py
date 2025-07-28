
import os
import logging
from flask import Flask, jsonify, request
import stripe

# Load your Stripe secret key from the environment
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)

@app.route("/")
def root():
    return "Stripe Render Server is running!"

@app.route("/product-catalog", methods=["GET"])
def product_catalog():
    # List active products and prices, expanding each price's product object
    products = stripe.Product.list(active=True).data
    prices   = stripe.Price.list(active=True, expand=["data.product"]).data

    catalog = []
    for price in prices:
        prod = price.product
        catalog.append({
            "price_id":    price.id,
            "unit_amount": price.unit_amount,
            "currency":    price.currency,
            "product": {
                "id":          prod.id,
                "name":        prod.name,
                "description": prod.description,
            }
        })

    return jsonify(catalog)

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json(force=True)
    price_id = data.get("priceId")
    quantity = data.get("quantity", 1)
    domain   = os.getenv("DOMAIN", "").rstrip("/")

    # Retrieve the Price to detect whether it's recurring
    price_obj = stripe.Price.retrieve(price_id)

    # Choose checkout mode based on whether the price is recurring
    if hasattr(price_obj, "recurring") and price_obj.recurring:
        mode = "subscription"
    else:
        mode = "payment"

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": quantity}],
        mode=mode,
        success_url=f"{domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{domain}/cancel",
    )
    return jsonify({"url": session.url})

# DEBUG: after defining all routes, log them
logging.basicConfig(level=logging.INFO)
for rule in app.url_map.iter_rules():
    logging.info(f"Route: {rule} -> methods={list(rule.methods)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
