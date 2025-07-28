# License‑Key‑Server

A simple Flask + Stripe server for listing products, creating checkout sessions, and handling license‑key webhooks.

## Endpoints

### `GET /product-catalog`  
Returns all active Stripe products & prices as JSON:
```json
[
  {
    "price_id": "price_1234",
    "unit_amount": 29900,
    "currency": "sgd",
    "product": {
      "id": "prod_ABC",
      "name": "Standard Plan",
      "description": "Monthly subscription"
    }
  },
  …
]
```

### `POST /create-checkout-session`  
Create a Stripe Checkout session.  
**Body**:  
```json
{ 
  "priceId": "price_1234", 
  "quantity": 1 
}
```  
**Response**:  
```json
{ 
  "url": "https://checkout.stripe.com/pay/cs_test_…" 
}
```

## Setup

1. Copy `.env.template` to `.env` and fill in your keys:
   ```bash
   cp .env.template .env
   ```
2. Edit `.env`:
   ```
   DOMAIN=https://your-render-url.onrender.com
   STRIPE_SECRET_KEY=sk_test_xxx_or_sk_live_xxx
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Run locally:
   ```bash
   python server.py
   ```
5. Or start with Gunicorn:
   ```bash
   gunicorn server:app
   ```

## Deployment

Deploy to Render (or your platform of choice) with:

- **Build Command**:  
  ```bash
  pip install -r requirements.txt
  ```
- **Start Command**:  
  ```bash
  gunicorn server:app
  ```

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) for details.
