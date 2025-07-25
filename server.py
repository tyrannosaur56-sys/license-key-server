
from flask import Flask, request, jsonify
import json
from datetime import datetime
from uuid import uuid4
import os
app = Flask(__name__)

CONFIG_PATH = 'config.json'
LICENSES_PATH = 'licenses.json'

def generate_license_key(tier):
    prefix = {
        "Lite": "ARLITE",
        "Standard": "ARSTD",
        "Pro": "ARPRO"
    }.get(tier, "ARUNK")
    return f"{prefix}-{uuid4().hex[:4]}-{uuid4().hex[:4]}-{uuid4().hex[:4]}"

@app.route('/webhook', methods=['POST'])
def webhook():
    event = request.get_json()
    try:
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']
            email = None
            price_id = None
            tier = "Unknown"

            # Extract email from custom_fields or customer_email
            custom_fields = session.get('custom_fields', [])
            for field in custom_fields:
                if field.get('key') == 'email':
                    email = field.get('text', {}).get('value')

            if not email:
                email = session.get('customer_email')

            # Map Stripe Price ID to internal tier
            price_id = session.get('line_items', [{}])[0].get('price', {}).get('id') if 'line_items' in session else None
            price_id = price_id or session.get('metadata', {}).get('price') or session.get('display_items', [{}])[0].get('price', {}).get('id')

            tier_map = {
                "price_1RnPZcR8YgSn3RHKALzxFU7vC": "Pro",
                "price_1RnPZcR8YgSn3RHKALzxFU7vD": "Standard",
                "price_1RnPZcR8YgSn3RHKALzxFU7vE": "Lite"
            }

            tier = tier_map.get(price_id, "Unknown")

            if not email:
                return jsonify({'error': 'Email not found'}), 400

            # Generate license
            license_key = generate_license_key(tier)
            record = {
                "email": email,
                "tier": tier,
                "key": license_key,
                "timestamp": datetime.utcnow().isoformat() + "Z"
            }

            try:
                with open(LICENSES_PATH, "r") as f:
                    data = json.load(f)
            except FileNotFoundError:
                data = {"licenses": []}

            data["licenses"].append(record)
            with open(LICENSES_PATH, "w") as f:
                json.dump(data, f, indent=2)

            return jsonify({"status": "success", "license": license_key}), 200
        else:
            return jsonify({"status": "ignored"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    if __name__ == '__main__':
        app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 4242)))




