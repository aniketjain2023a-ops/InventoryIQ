import os
import smtplib
from email.message import EmailMessage

SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_EMAIL = os.getenv("SMTP_EMAIL", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")

def send_purchase_order_email(
    recipient_email,
    po_number,
    supplier_name,
    quantity,
):
    msg = EmailMessage()

    msg["Subject"] = f"Purchase Order {po_number}"
    msg["From"] = SMTP_EMAIL
    msg["To"] = recipient_email

    msg.set_content(
        f"""
Dear {supplier_name or 'Supplier'},

Please process the following purchase order.

PO Number: {po_number}
Quantity: {quantity}

Regards,
InventoryIQ
"""
    )

    if not SMTP_EMAIL or not SMTP_PASSWORD:
        raise ValueError(
            "SMTP_EMAIL and SMTP_PASSWORD environment variables are not configured"
        )

    with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.login(
            SMTP_EMAIL,
            SMTP_PASSWORD,
        )
        smtp.send_message(msg)

    return True


def test_email_connection():
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        return False, "SMTP credentials not configured"

    try:
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as smtp:
            smtp.login(SMTP_EMAIL, SMTP_PASSWORD)
        return True, "Connection successful"
    except Exception as e:
        return False, str(e)