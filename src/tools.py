import functools
import json
import os
from typing import Any, Dict

_DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")

# Module-level cache so JSON is read once per process, not per tool call
_ORDERS: Dict | None = None
_PRODUCTS: Dict | None = None


def _load(filename: str) -> Dict:
    with open(os.path.join(_DATA_DIR, filename), encoding="utf-8") as f:
        return json.load(f)


def _orders() -> Dict:
    global _ORDERS
    if _ORDERS is None:
        _ORDERS = _load("orders.json")
    return _ORDERS


def _products() -> Dict:
    global _PRODUCTS
    if _PRODUCTS is None:
        _PRODUCTS = _load("products.json")
    return _PRODUCTS


def lookup_order(order_id: str) -> Dict[str, Any]:
    """Return order details for the given order ID."""
    orders = _orders()
    key = order_id.strip().upper()
    if key in orders:
        return {"found": True, "order": orders[key]}
    return {"found": False, "message": f"No order found with ID '{order_id}'. Please verify the order number."}


def lookup_product(product_query: str) -> Dict[str, Any]:
    """Search the product catalogue by name or product ID."""
    products = _products()
    query = product_query.strip()

    # Exact product-ID match
    if query.upper() in products:
        return {"found": True, "products": [products[query.upper()]]}

    # Partial name match (EN or AR)
    q_lower = query.lower()
    matches = [
        p for p in products.values()
        if q_lower in p["name"].lower() or q_lower in p.get("name_ar", "").lower()
    ]
    if matches:
        return {"found": True, "products": matches[:3]}

    return {"found": False, "message": f"No products found matching '{product_query}'."}


@functools.lru_cache(maxsize=1)
def get_return_policy() -> Dict[str, Any]:
    """Return Mumzworld's current return, exchange, and refund policy."""
    return {
        "return_window_days": 30,
        "exchange_window_days": 30,
        "refund_timeline": "5–7 business days after item received at warehouse",
        "conditions": [
            "Item must be unused and in original, undamaged packaging",
            "Proof of purchase (order confirmation or receipt) required",
            "Items must be returned with all accessories and manuals",
        ],
        "non_returnable_categories": [
            "baby_formula (hygiene)",
            "personal_care products once opened",
            "underwear / swimwear",
            "sale / clearance items (unless defective)",
        ],
        "damaged_on_delivery": "Customer must report within 48 hours of delivery; full replacement or refund issued",
        "warranty_claims": "Manufacturer warranty handled separately; contact Mumzworld CS to initiate",
        "how_to_initiate": "Log in → My Orders → Request Return, or email customercare@mumzworld.com",
        "prepaid_label": "Prepaid return label emailed within 24 hours of approved request",
        "contact": {
            "email": "customercare@mumzworld.com",
            "whatsapp": "+971-4-XXX-XXXX",
            "hours": "Sun–Thu 9am–6pm GST",
        },
    }


# ── Tool definitions (OpenAI function-calling format) ──────────────────────────

TOOL_SPECS = [
    {
        "type": "function",
        "function": {
            "name": "lookup_order",
            "description": (
                "Look up order details by order ID. Use whenever the customer mentions "
                "an order number (e.g. MW-10021). Returns status, items, delivery date, "
                "payment method, and return eligibility."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "The order ID to look up, e.g. 'MW-10021'",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_product",
            "description": (
                "Search the Mumzworld product catalogue by product name or product ID. "
                "Returns price, stock status, return eligibility, and both EN and AR descriptions."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "product_query": {
                        "type": "string",
                        "description": "Product name (partial is fine) or product ID, e.g. 'Cybex Gazelle' or 'P-STR-001'",
                    }
                },
                "required": ["product_query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_return_policy",
            "description": (
                "Retrieve Mumzworld's current return, exchange, and refund policy. "
                "Call this whenever the customer asks about returns, refunds, or exchanges."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

TOOL_REGISTRY = {
    "lookup_order": lookup_order,
    "lookup_product": lookup_product,
    "get_return_policy": get_return_policy,
}
