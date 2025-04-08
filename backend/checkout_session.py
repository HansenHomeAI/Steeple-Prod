import os
import json
import stripe
import uuid
import logging

# Set up logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize Stripe with your secret key
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Default URLs for GitHub Pages
DEFAULT_SUCCESS_URL = "https://hansenhomeai.github.io/success.html"
DEFAULT_CANCEL_URL = "https://hansenhomeai.github.io/cancel.html"

def create_cors_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, Origin, X-Requested-With',
            'Access-Control-Max-Age': '3600',
            'Content-Type': 'application/json'
        },
        'body': json.dumps(body)
    }

def handler(event, context):
    logger.info("Received event: %s", json.dumps(event))
    
    # Handle CORS preflight request
    if event.get('httpMethod') == 'OPTIONS':
        logger.info("Handling OPTIONS request")
        return {
            'statusCode': 200,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '3600'
            },
            'body': ''
        }

    try:
        # Log the incoming request details
        logger.info("Request headers: %s", event.get('headers', {}))
        logger.info("Request body: %s", event.get('body', '{}'))

        body = json.loads(event.get("body", "{}"))
        items = body.get("items", [])
        customer_email = body.get("customerEmail")

        if not items:
            raise ValueError("No items provided in the request")

        # Build Stripe line items array
        line_items = []
        for item in items:
            line_items.append({
                "price_data": {
                    "currency": "usd",
                    "product_data": {
                        "name": item.get("name"),
                    },
                    "unit_amount": int(float(item.get("price")) * 100),
                },
                "quantity": item.get("quantity"),
            })

        # Get URLs from environment variables or use defaults
        success_url = os.environ.get("SUCCESS_URL") or DEFAULT_SUCCESS_URL
        cancel_url = os.environ.get("CANCEL_URL") or DEFAULT_CANCEL_URL

        logger.info(f"Using success_url: {success_url}")
        logger.info(f"Using cancel_url: {cancel_url}")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            customer_email=customer_email,
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                "order_id": str(uuid.uuid4())
            },
            # Add appearance customizations with brand colors
            appearance={
                "theme": "flat",
                "variables": {
                    "colorPrimary": "#256F8A",  # Your brand blue for primary actions
                    "colorBackground": "#EFEEE7",  # Your main background color
                    "colorText": "#1E1E1E",  # Your brand black for text
                    "colorDanger": "#BA3B1A",  # Your brand red for errors/alerts
                    "colorButtonText": "#FFFFFF",  # White text on buttons for contrast
                    "borderRadius": "4px",
                    "spacingUnit": "4px",
                    "fontFamily": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
                },
                "rules": {
                    ".Tab": {
                        "borderColor": "#D9D9D9",
                        "backgroundColor": "#EFEEE7"
                    },
                    ".Tab--selected": {
                        "borderColor": "#256F8A",
                        "backgroundColor": "#EFEEE7"
                    },
                    ".Input": {
                        "borderColor": "#D9D9D9"
                    },
                    ".Input:focus": {
                        "borderColor": "#256F8A"
                    }
                }
            },
            # Add custom text
            custom_text={
                "submit": {
                    "message": "Thank you for supporting Bauhaus Poster Shop!"
                }
            },
            # Add shipping options if needed
            shipping_options=[
                {
                    "shipping_rate_data": {
                        "type": "fixed_amount",
                        "fixed_amount": {
                            "amount": 0,
                            "currency": "usd"
                        },
                        "display_name": "Free shipping"
                    }
                }
            ],
            # Add customer details collection
            billing_address_collection="required",
            shipping_address_collection={
                "allowed_countries": ["US", "CA", "GB", "DE", "FR", "IT", "ES", "NL", "BE", "DK", "SE", "NO", "FI", "AT", "CH", "IE", "PT", "GR", "CZ", "HU", "PL", "SK", "SI", "HR", "RO", "BG", "EE", "LV", "LT", "MT", "CY", "LU", "IS", "LI", "MC", "SM", "VA", "AD"]
            }
        )
        
        logger.info("Successfully created Stripe session: %s", session.id)
        
        return {
            "statusCode": 200,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '3600',
                'Content-Type': 'application/json'
            },
            "body": json.dumps({"sessionId": session.id})
        }
    except Exception as e:
        logger.error("Error processing checkout: %s", str(e))
        return {
            "statusCode": 400,
            "headers": {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization',
                'Access-Control-Max-Age': '3600',
                'Content-Type': 'application/json'
            },
            "body": json.dumps({"error": str(e)})
        } 