# test_legacy_checkout.py

from legacy_checkout import process_order


def test_regular_customer():
    customer = {
        "name": "Ana",
        "type": "regular"
    }

    items = [
        {
            "name": "Notebook",
            "price": 1000.00,
            "qty": 1,
            "weight": 2
        }
    ]

    result = process_order(
        customer,
        items,
        state="MG"
    )

    assert result["subtotal"] == 1000.00
    assert result["discount"] == 50.00
    assert result["shipping"] == 0
    assert result["tax"] == 66.50
    assert result["total"] == 1016.50


def test_vip_customer():
    customer = {
        "name": "Carlos",
        "type": "vip"
    }

    items = [
        {
            "name": "Monitor",
            "price": 600,
            "qty": 2,
            "weight": 3
        }
    ]

    result = process_order(
        customer,
        items,
        state="SP"
    )

    assert result["subtotal"] == 1200
    assert result["discount"] == 180


def test_coupon():
    customer = {
        "name": "Maria",
        "type": "regular"
    }

    items = [
        {
            "name": "Teclado",
            "price": 200,
            "qty": 2,
            "weight": 1
        }
    ]

    result = process_order(
        customer,
        items,
        coupon="PROMO10",
        state="MG"
    )

    assert result["discount"] == 40


def test_duplicate_products():
    customer = {
        "name": "João",
        "type": "regular"
    }

    items = [
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Mouse", "price": 100, "qty": 1, "weight": 0.2},
        {"name": "Teclado", "price": 200, "qty": 1, "weight": 1}
    ]

    result = process_order(customer, items)

    assert result["duplicate_products"] == ["Mouse"]
    
##testes novos

def test_funcionario():
    customer = {"name": "Joaozinho", "type": "employee"}
    items = [{"name": "Cadeira", "price": 300.00, "qty": 2, "weight": 5}]

    result = process_order(customer, items, state="MG")

    assert result["customer"] == "Joaozinho"
    assert result["subtotal"] == 600.00
    assert result["discount"] == 120.00
    assert result["shipping"] == 0
    assert result["tax"] == 33.60
    assert result["total"] == 513.60
    assert result["points"] == 51


def test_fretegratis():
    customer = {"name": "Maria", "type": "regular"}
    items = [{"name": "Headset", "price": 500.00, "qty": 1, "weight": 3}]

    result = process_order(customer, items, state="RJ")

    assert result["subtotal"] == 500.00
    assert result["discount"] == 0
    assert result["shipping"] == 0
    assert result["tax"] == 40.00
    assert result["total"] == 540.00
    assert result["points"] == 54

def test_desconto_25_por_cento():
    customer = {"name": "Joana", "type": "employee"}
    items = [{"name": "Cadeira", "price": 300.00, "qty": 2, "weight": 5}]

    result = process_order(customer, items, coupon="PROMO10", state="MG")

    assert result["discount"] == 150.00
    assert result["discount"] == result["subtotal"] * 0.25
    assert result["total"] == 481.50


def test_desconto_exatamente_no_limite():
    customer = {"name": "Carlos", "type": "vip"}
    items = [
        {"name": "Teclado", "price": 500.00, "qty": 1, "weight": 1},
        {"name": "Mouse", "price": 500.00, "qty": 1, "weight": 1},
    ]

    result = process_order(customer, items, coupon="PROMO10", state="SP")

    assert result["subtotal"] == 1000.00
    assert result["discount"] == 250.00
    assert result["tax"] == 67.50      # (1000 - 250) * 0.09
    assert result["total"] == 817.50
    assert result["points"] == 163


def test_desconto_com_cupom():
    customer = {"name": "Carla", "type": "vip"}
    items = [{"name": "Webcam", "price": 300.00, "qty": 1, "weight": 2}]

    result = process_order(customer, items, coupon="VIP50", state="MG")

    assert result["discount"] == 75.00
    assert result["shipping"] == 20.80  # 300 < 500 => 20 + 2 * 0.4
    assert result["tax"] == 15.75
    assert result["total"] == 261.55
    assert result["points"] == 52
    
    
def test_cupom_promo20():
    # subtotal 600 >= 500 => PROMO20 soma 20% (120); regular nao bate o minimo de 800
    customer = {"name": "Pedro", "type": "regular"}
    items = [{"name": "Cadeira", "price": 600.00, "qty": 1, "weight": 1}]

    result = process_order(customer, items, coupon="PROMO20", state="MG")

    assert result["discount"] == 120.00
    assert result["tax"] == 33.60      # (600 - 120) * 0.07
    assert result["total"] == 513.60
    assert result["points"] == 51


def test_frete_fora_do_sudeste():
    # BA nao esta em TAX_RATES => 35 + peso 1 * 0.6 = 35.60, imposto 12% = 48.00
    customer = {"name": "Pedro", "type": "regular"}
    items = [{"name": "Cadeira", "price": 400.00, "qty": 1, "weight": 1}]

    result = process_order(customer, items, state="BA")

    assert result["shipping"] == 35.60
    assert result["tax"] == 48.00
    assert result["total"] == 483.60
    assert result["points"] == 48


def test_frete_expresso():
    # subtotal 600 daria frete gratis, mas express=True cobra: (20 + 2 * 0.4) * 1.8 = 37.44
    customer = {"name": "Pedro", "type": "regular"}
    items = [{"name": "Cadeira", "price": 600.00, "qty": 1, "weight": 2}]

    result = process_order(customer, items, state="MG", express=True)

    assert result["shipping"] == 37.44
    assert result["tax"] == 42.00
    assert result["total"] == 679.44
    assert result["points"] == 67

    
