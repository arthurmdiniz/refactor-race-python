# legacy_checkout.py

ORDERS_PROCESSED = []

#declarar tudo antes
TAX_RATES = {
    "MG": 0.07,
    "SP": 0.09,
    "RJ": 0.08,
    "ES": 0.07,
}
DEFAULT_TAX_RATE = 0.12

#frete
FREE_SHIPPING_MIN = 500.0
SE_BASE_FEE = 20.0
SE_WEIGHT_MULTIPLIER = 0.4
OTHER_BASE_FEE = 35.0
OTHER_WEIGHT_MULTIPLIER = 0.6
EXPRESS_SHIPPING_MULTIPLIER = 1.8

#desconto
VIP_DISCOUNT_RATE = 0.10
VIP_DISCOUNT_RATE_HIGH = 0.15
VIP_HIGH_THRESHOLD = 1000.0
EMPLOYEE_DISCOUNT_RATE = 0.20
REGULAR_DISCOUNT_RATE = 0.05
REGULAR_MIN_SUBTOTAL = 800.0
MAX_DISCOUNT_RATE = 0.25

#cupons
COUPON_PROMO10 = "PROMO10"
COUPON_PROMO10_RATE = 0.10
COUPON_PROMO20 = "PROMO20"
COUPON_PROMO20_RATE = 0.20
COUPON_PROMO20_MIN_SUBTOTAL = 500.0
COUPON_VIP50 = "VIP50"
COUPON_VIP50_AMOUNT = 50.0

#pontos fidelidade
VIP_POINTS_DIVISOR = 5
POINTS_DIVISOR = 10


def calculate_subtotal(items):
    return sum(
        item["price"] * item["qty"]
        for item in items
        if item["qty"] > 0
    )


def calculate_discount(customer, subtotal, coupon):
    customer_type = customer["type"]

    if customer_type == "vip":
        discount_rate = (
            VIP_DISCOUNT_RATE_HIGH
            if subtotal >= VIP_HIGH_THRESHOLD
            else VIP_DISCOUNT_RATE
        )
        discount = subtotal * discount_rate
    elif customer_type == "employee":
        discount = subtotal * EMPLOYEE_DISCOUNT_RATE
    elif customer_type == "regular" and subtotal >= REGULAR_MIN_SUBTOTAL:
        discount = subtotal * REGULAR_DISCOUNT_RATE
    else:
        discount = 0

    if coupon == COUPON_PROMO10:
        discount += subtotal * COUPON_PROMO10_RATE
    elif coupon == COUPON_PROMO20 and subtotal >= COUPON_PROMO20_MIN_SUBTOTAL:
        discount += subtotal * COUPON_PROMO20_RATE
    elif coupon == COUPON_VIP50 and customer_type == "vip":
        discount += COUPON_VIP50_AMOUNT

    return min(discount, subtotal * MAX_DISCOUNT_RATE)


def calculate_total_weight(items):
    return sum(item.get("weight", 0) * item["qty"] for item in items)


def calculate_shipping(subtotal, total_weight, state, express):
    if subtotal >= FREE_SHIPPING_MIN and not express:
        return 0

    if state in TAX_RATES:
        shipping = SE_BASE_FEE + total_weight * SE_WEIGHT_MULTIPLIER
    else:
        shipping = OTHER_BASE_FEE + total_weight * OTHER_WEIGHT_MULTIPLIER

    if express:
        shipping *= EXPRESS_SHIPPING_MULTIPLIER

    return shipping


def calculate_tax(discounted_value, state):
    tax_rate = TAX_RATES.get(state, DEFAULT_TAX_RATE)
    return discounted_value * tax_rate


def calculate_points(customer_type, discounted_value, shipping, tax):
    divisor = VIP_POINTS_DIVISOR if customer_type == "vip" else POINTS_DIVISOR
    return int((discounted_value + shipping + tax) / divisor)


def find_duplicate_products(items):
    product_counts = {}
    for item in items:
        product_name = item["name"]
        product_counts[product_name] = product_counts.get(product_name, 0) + 1

    return [name for name, count in product_counts.items() if count > 1]


def process_order(customer, items, coupon="", state="MG", express=False):
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(customer, subtotal, coupon)
    discounted_value = subtotal - discount
    total_weight = calculate_total_weight(items)
    shipping = calculate_shipping(subtotal, total_weight, state, express)
    tax = calculate_tax(discounted_value, state)
    points = calculate_points(customer["type"], discounted_value, shipping, tax)
    duplicate_products = find_duplicate_products(items)
    total = round(discounted_value + shipping + tax, 2)

    result = {
        "customer": customer["name"],
        "subtotal": round(subtotal, 2),
        "discount": round(discount, 2),
        "shipping": round(shipping, 2),
        "tax": round(tax, 2),
        "total": total,
        "points": points,
        "duplicate_products": duplicate_products
    }

    ORDERS_PROCESSED.append(result)
    return result