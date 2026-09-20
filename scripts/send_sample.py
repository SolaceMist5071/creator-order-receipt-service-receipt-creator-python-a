import os

from creator_receipts.infrai_email import InfraiEmail
from creator_receipts.receipt_sender import PaidOrder, send_paid_order_receipt


def main() -> None:
    recipient = os.environ.get("DEMO_EMAIL_TO")
    if not recipient:
        raise SystemExit("DEMO_EMAIL_TO is required")

    order = PaidOrder.model_validate(
        {
            "order_id": "ORDER-1042",
            "buyer_email": recipient,
            "creator_name": "Northline Studio",
            "amount_cents": 2400,
            "currency": "USD",
            "payment_state": "paid",
            "assets": [
                {
                    "title": "Field Notes PDF",
                    "download_url": "https://downloads.example.com/orders/ORDER-1042/notes",
                }
            ],
            "subscriber_update": {
                "list_name": "studio notes",
                "state": "subscribed",
            },
        }
    )
    client = InfraiEmail()
    try:
        result = send_paid_order_receipt(order, client)
        print(result.model_dump_json(indent=2))
    finally:
        client.close()


if __name__ == "__main__":
    main()

