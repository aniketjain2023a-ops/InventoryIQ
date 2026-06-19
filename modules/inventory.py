from database.db import SessionLocal
from database.models import Product, Transaction, PurchaseOrder
from datetime import datetime

from uuid import uuid4
import os
try:
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet
    REPORTLAB_AVAILABLE = True
except ImportError:
    SimpleDocTemplate = None
    Paragraph = None
    Spacer = None
    getSampleStyleSheet = None
    REPORTLAB_AVAILABLE = False


def get_product_by_id(product_id):
    db = SessionLocal()
    try:
        return db.query(Product).filter(Product.id == product_id).first()
    finally:
        db.close()


def add_product(
    sku,
    name,
    category,
    unit_price,
    reorder_level,
    supplier_name=None,
    supplier_email=None,
    supplier_phone=None,
    lead_time_days=0,
):
    db = SessionLocal()
    try:
        sku = sku.strip()
        existing_product = (
            db.query(Product)
            .filter(Product.sku == sku)
            .first()
        )

        if existing_product:
            return False

        product = Product(
            sku=sku,
            name=name,
            category=category,
            unit_price=unit_price,
            reorder_level=reorder_level,
            quantity=0,
            supplier_name=supplier_name,
            supplier_email=supplier_email,
            supplier_phone=supplier_phone,
            lead_time_days=lead_time_days,
        )
        db.add(product)
        db.commit()
        return True
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_product(product_id):
    db = SessionLocal()
    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if not product:
            return False

        db.delete(product)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_product(
    product_id,
    name,
    category,
    unit_price,
    reorder_level,
    supplier_name,
    supplier_email,
    supplier_phone,
    lead_time_days,
):
    db = SessionLocal()
    try:
        product = (
            db.query(Product)
            .filter(Product.id == product_id)
            .first()
        )

        if not product:
            return False

        product.name = name
        product.category = category
        product.unit_price = unit_price
        product.reorder_level = reorder_level
        product.supplier_name = supplier_name
        product.supplier_email = supplier_email
        product.supplier_phone = supplier_phone
        product.lead_time_days = lead_time_days

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_products():
    db = SessionLocal()
    try:
        return db.query(Product).all()
    finally:
        db.close()


def increase_quantity(product_id, amount):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        product.quantity = (product.quantity or 0) + amount

        db.add(Transaction(
            product_id=product.id,
            transaction_type="IN",
            quantity=amount,
            timestamp=datetime.utcnow(),
        ))
        db.commit()
        return True
    finally:
        db.close()


def decrease_quantity(product_id, amount):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()
        if not product:
            return False

        current_qty = product.quantity or 0
        if current_qty < amount:
            return False

        product.quantity = current_qty - amount

        db.add(Transaction(
            product_id=product.id,
            transaction_type="OUT",
            quantity=amount,
            timestamp=datetime.utcnow(),
        ))
        db.commit()
        return True
    finally:
        db.close()


def get_inventory_summary():
    products = get_products()

    return {
        "total_products": len(products),
        "total_quantity": sum((getattr(p, 'quantity', 0) or 0) for p in products),
        "total_value": sum((getattr(p, 'quantity', 0) or 0) * (p.unit_price or 0) for p in products),
        "low_stock": sum(
            1 for p in products
            if (getattr(p, 'quantity', 0) or 0) <= (p.reorder_level or 0)
        ),
    }


def get_stock_status(product):
    quantity = getattr(product, 'quantity', 0) or 0
    reorder_level = product.reorder_level or 0

    if quantity == 0:
        return "🔴 Out of Stock"
    if quantity <= reorder_level:
        return "🟠 Reorder Required"
    if quantity <= reorder_level * 1.5:
        return "🟡 Low Stock"
    return "🟢 Healthy"


def get_inventory_table_data():
    return [{
        "SKU": p.sku,
        "Name": p.name,
        "Category": p.category,
        "Supplier": getattr(p, 'supplier_name', '') or '-',
        "Lead Time (Days)": getattr(p, 'lead_time_days', 0) or 0,
        "Quantity": getattr(p, 'quantity', 0) or 0,
        "Unit Price": p.unit_price or 0,
        "Inventory Value": (getattr(p, 'quantity', 0) or 0) * (p.unit_price or 0),
        "Reorder Level": p.reorder_level or 0,
        "Status": get_stock_status(p),
    } for p in get_products()]


def get_low_stock_products():
    return [
        p for p in get_products()
        if (getattr(p, 'quantity', 0) or 0) <= (p.reorder_level or 0)
    ]


def get_supplier_directory():
    suppliers = {}

    for product in get_products():
        supplier_name = getattr(product, "supplier_name", None)

        if not supplier_name:
            continue

        if supplier_name not in suppliers:
            suppliers[supplier_name] = {
                "Supplier": supplier_name,
                "Products Supplied": 0,
                "Email": getattr(product, "supplier_email", "") or "-",
                "Phone": getattr(product, "supplier_phone", "") or "-",
                "Avg Lead Time": 0,
                "_lead_times": [],
            }

        suppliers[supplier_name]["Products Supplied"] += 1

        lead_time = getattr(product, "lead_time_days", 0) or 0
        suppliers[supplier_name]["_lead_times"].append(lead_time)

    results = []

    for supplier in suppliers.values():
        lead_times = supplier.pop("_lead_times")

        supplier["Avg Lead Time"] = round(
            sum(lead_times) / len(lead_times),
            1,
        ) if lead_times else 0

        results.append(supplier)

    return sorted(results, key=lambda x: x["Supplier"])


def get_reorder_recommendations():
    recommendations = []

    for product in get_products():
        quantity = getattr(product, "quantity", 0) or 0
        reorder_level = product.reorder_level or 0

        if quantity > reorder_level:
            continue

        recommendations.append({
            "id": product.id,
            "product": product.name,
            "sku": product.sku,
            "supplier": getattr(product, "supplier_name", "") or "-",
            "supplier_email": getattr(product, "supplier_email", "") or "",
            "supplier_phone": getattr(product, "supplier_phone", "") or "",
            "current_stock": quantity,
            "reorder_level": reorder_level,
            "lead_time_days": getattr(product, "lead_time_days", 0) or 0,
            "status": (
                "🔴 Reorder Immediately"
                if quantity == 0
                else "🟠 Reorder Soon"
            ),
        })

    return recommendations


def create_purchase_order(product_id, quantity):
    db = SessionLocal()
    try:
        product = db.query(Product).filter(Product.id == product_id).first()

        if not product:
            return False

        po = PurchaseOrder(
            po_number=f"PO-{uuid4().hex[:8].upper()}",
            product_id=product.id,
            supplier_name=getattr(product, "supplier_name", "Unknown"),
            supplier_email=getattr(product, "supplier_email", "") or "",
            supplier_phone=getattr(product, "supplier_phone", "") or "",
            lead_time_days=getattr(product, "lead_time_days", 0) or 0,
            unit_price=product.unit_price or 0,
            quantity=quantity,
            status="Draft",
        )

        db.add(po)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_purchase_orders():
    db = SessionLocal()
    try:
        purchase_orders = (
            db.query(PurchaseOrder)
            .order_by(PurchaseOrder.created_at.desc())
            .all()
        )

        for po in purchase_orders:
            _ = po.id

        return purchase_orders
    finally:
        db.close()


def update_purchase_order_status(po_id, status):
    db = SessionLocal()
    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return False

        po.status = status

        if status == "Delivered":
            po.is_closed = True

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



def mark_purchase_order_sent(po_id):
    db = SessionLocal()
    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return False

        po.status = "Sent"
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# New function: receive_purchase_order
def receive_purchase_order(po_id):
    db = SessionLocal()
    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return False

        product = (
            db.query(Product)
            .filter(Product.id == po.product_id)
            .first()
        )

        if not product:
            return False

        product.quantity = (product.quantity or 0) + (po.quantity or 0)

        db.add(Transaction(
            product_id=product.id,
            transaction_type="IN",
            quantity=po.quantity,
            timestamp=datetime.utcnow(),
        ))

        po.status = "Delivered"

        if hasattr(po, "is_closed"):
            po.is_closed = True

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


# New function: delete_purchase_order
def delete_purchase_order(po_id):
    db = SessionLocal()
    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return False

        db.delete(po)
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()



def get_purchase_order_total(po):
    return (getattr(po, "quantity", 0) or 0) * (
        getattr(po, "unit_price", 0) or 0
    )


def generate_purchase_order_pdf(po_id):
    if not REPORTLAB_AVAILABLE:
        return None
    db = SessionLocal()
    try:
        po = (
            db.query(PurchaseOrder)
            .filter(PurchaseOrder.id == po_id)
            .first()
        )

        if not po:
            return None

        product = (
            db.query(Product)
            .filter(Product.id == po.product_id)
            .first()
        )

        pdf_dir = "generated_pos"
        os.makedirs(pdf_dir, exist_ok=True)

        pdf_path = os.path.join(
            pdf_dir,
            f"{po.po_number}.pdf"
        )

        doc = SimpleDocTemplate(pdf_path)
        styles = getSampleStyleSheet()

        elements = []

        elements.append(
            Paragraph("InventoryIQ Purchase Order", styles["Title"])
        )
        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(f"PO Number: {po.po_number}", styles["Normal"])
        )
        elements.append(
            Paragraph(f"Status: {po.status}", styles["Normal"])
        )
        elements.append(
            Paragraph(
                f"Created: {po.created_at.strftime('%d-%b-%Y') if po.created_at else '-'}",
                styles["Normal"],
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"Supplier: {po.supplier_name or '-'}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                f"Email: {po.supplier_email or '-'}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(
                f"Phone: {po.supplier_phone or '-'}",
                styles["Normal"],
            )
        )

        elements.append(Spacer(1, 12))

        elements.append(
            Paragraph(
                f"Product: {product.name if product else 'Unknown'}",
                styles["Normal"],
            )
        )
        elements.append(
            Paragraph(f"Quantity: {po.quantity}", styles["Normal"])
        )
        elements.append(
            Paragraph(f"Unit Price: ₹{po.unit_price:,.2f}", styles["Normal"])
        )
        elements.append(
            Paragraph(
                f"Total Value: ₹{get_purchase_order_total(po):,.2f}",
                styles["Normal"],
            )
        )

        doc.build(elements)
        return pdf_path

    finally:
        db.close()


def get_top_inventory_products(limit=5):
    return sorted(
        get_products(),
        key=lambda p: (getattr(p, 'quantity', 0) or 0) * (p.unit_price or 0),
        reverse=True,
    )[:limit]


def get_inventory_health_score():
    products = get_products()
    if not products:
        return 100

    score = 100
    for p in products:
        quantity = getattr(p, 'quantity', 0) or 0
        reorder_level = p.reorder_level or 0
        lead_time = getattr(p, 'lead_time_days', 0) or 0

        if quantity == 0:
            score -= 20
        elif quantity <= reorder_level:
            score -= 10
            if lead_time > 7:
                score -= 5
        elif quantity <= reorder_level * 1.5:
            score -= 5

    return max(0, min(100, round(score)))


def get_ai_insights():
    products = get_products()
    if not products:
        return ["Inventory database is empty."]

    insights = []
    low_stock = get_low_stock_products()
    if low_stock:
        insights.append(f"{len(low_stock)} product(s) require immediate replenishment.")

    top_product = max(
        products,
        key=lambda p: (getattr(p, 'quantity', 0) or 0) * (p.unit_price or 0),
    )
    insights.append(f"Highest inventory value item: {top_product.name}.")

    health = get_inventory_health_score()
    insights.append(
        "Inventory health is excellent." if health >= 90
        else "Inventory health is stable but should be monitored." if health >= 70
        else "Inventory health is at risk. Review stock levels."
    )
    return insights


def get_daily_consumption_rate(product_id, days=30):
    db = SessionLocal()
    try:
        transactions = (
            db.query(Transaction)
            .filter(
                Transaction.product_id == product_id,
                Transaction.transaction_type == "OUT",
            )
            .all()
        )

        if not transactions:
            return 0.0

        total_consumed = sum(t.quantity or 0 for t in transactions)

        first_date = min(
            t.timestamp for t in transactions if t.timestamp is not None
        )
        last_date = max(
            t.timestamp for t in transactions if t.timestamp is not None
        )

        active_days = max((last_date - first_date).days + 1, 1)

        return round(total_consumed / active_days, 2)
    finally:
        db.close()



def get_stockout_forecasts():
    forecasts = []

    for product in get_products():
        quantity = getattr(product, "quantity", 0) or 0
        consumption_rate = get_daily_consumption_rate(product.id)

        if consumption_rate <= 0:
            days_remaining = None
            risk = "🟢 Low"
        else:
            days_remaining = round(quantity / consumption_rate, 1)

            if days_remaining < 7:
                risk = "🔴 Critical"
            elif days_remaining < 15:
                risk = "🟠 High"
            elif days_remaining < 30:
                risk = "🟡 Medium"
            else:
                risk = "🟢 Low"

        forecasts.append({
            "product": product.name,
            "current_stock": quantity,
            "daily_consumption": consumption_rate,
            "days_remaining": days_remaining,
            "risk": risk,
        })

    return forecasts


# Fast/Slow moving products
def get_fast_moving_products(limit=5):
    db = SessionLocal()
    try:
        movement = {}

        transactions = (
            db.query(Transaction)
            .filter(Transaction.transaction_type == "OUT")
            .all()
        )

        for txn in transactions:
            movement[txn.product_id] = movement.get(txn.product_id, 0) + (txn.quantity or 0)

        results = []

        for product_id, qty in movement.items():
            product = db.query(Product).filter(Product.id == product_id).first()
            if product:
                results.append({
                    "product": product.name,
                    "quantity_removed": qty,
                })

        return sorted(
            results,
            key=lambda x: x["quantity_removed"],
            reverse=True,
        )[:limit]

    finally:
        db.close()


def get_slow_moving_products(limit=5):
    db = SessionLocal()
    try:
        movement = {}

        transactions = (
            db.query(Transaction)
            .filter(Transaction.transaction_type == "OUT")
            .all()
        )

        for txn in transactions:
            movement[txn.product_id] = movement.get(txn.product_id, 0) + (txn.quantity or 0)

        results = []

        for product in db.query(Product).all():
            results.append({
                "product": product.name,
                "quantity_removed": movement.get(product.id, 0),
            })

        return sorted(
            results,
            key=lambda x: x["quantity_removed"],
        )[:limit]

    finally:
        db.close()


def get_transactions(limit=100):
    db = SessionLocal()
    try:
        return db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit).all()
    finally:
        db.close()


def get_transaction_table_data(limit=100):
    db = SessionLocal()
    try:
        transactions = db.query(Transaction).order_by(Transaction.timestamp.desc()).limit(limit).all()
        rows = []
        for txn in transactions:
            product = db.query(Product).filter(Product.id == txn.product_id).first()
            rows.append({
                "Timestamp": txn.timestamp.strftime("%d-%b-%Y %H:%M") if txn.timestamp else "-",
                "Product": product.name if product else f"Product #{txn.product_id}",
                "Type": "🟢 IN" if txn.transaction_type == "IN" else "🔴 OUT",
                "Quantity": txn.quantity,
            })
        return rows
    finally:
        db.close()


__all__ = [
    "add_product",
    "delete_product",
    "update_product",
    "get_products",
    "get_product_by_id",
    "increase_quantity",
    "decrease_quantity",
    "get_inventory_summary",
    "get_inventory_table_data",
    "get_supplier_directory",
    "get_reorder_recommendations",
    "create_purchase_order",
    "get_purchase_orders",
    "update_purchase_order_status",
    "mark_purchase_order_sent",
    "receive_purchase_order",
    "delete_purchase_order",
    "get_purchase_order_total",
    "generate_purchase_order_pdf",
    "get_transactions",
    "get_transaction_table_data",
    "get_stock_status",
    "get_low_stock_products",
    "get_top_inventory_products",
    "get_inventory_health_score",
    "get_ai_insights",
    "get_daily_consumption_rate",
    "get_fast_moving_products",
    "get_slow_moving_products",
    "get_stockout_forecasts",
]
