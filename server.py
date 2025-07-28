import os
import logging
from flask import Flask, jsonify, request
import stripe

# Initialize Stripe
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")

app = Flask(__name__)

@app.route("/")
def root():
    return "Stripe Render Server is running!"

@app.route("/product-catalog", methods=["GET"])
def product_catalog():
    products = stripe.Product.list(active=True).data
    prices = stripe.Price.list(active=True, expand=["data.product"]).data
    catalog = []
    for price in prices:
        prod = price.product
        catalog.append({
            "price_id": price.id,
            "unit_amount": price.unit_amount,
            "currency": price.currency,
            "product": {
                "id":          prod.id,
                "name":        prod.name,
                "description": prod.description,
            }
        })
    return jsonify(catalog)

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    price_id = data.get("priceId")
    quantity = data.get("quantity", 1)
    domain = os.getenv("DOMAIN", "https://your-domain.com")
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{"price": price_id, "quantity": quantity}],
        mode="payment",
        success_url=f"{domain}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{domain}/cancel",
    )
    return jsonify({"url": session.url})

# DEBUG: log all registered routes _after_ defining them
logging.basicConfig(level=logging.INFO)
for rule in app.url_map.iter_rules():
    logging.info(f"Route: {rule} -> methods={list(rule.methods)}")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

