from typing import Any

import pytest

from creator_receipts.receipt_sender import PaidOrder, send_paid_order_receipt


class RecordingEmail:
    def __init__(self) -> None:
        self.call: dict[str, Any] | None = None

    def send(self, **kwargs: Any) -> str:
        self.call = kwargs
        return "msg_receipt_1042"


def order(state: str = "paid") -> PaidOrder:
    return PaidOrder.model_validate(
        {
            "order_id": "ORDER-1042",
            "buyer_email": "buyer@example.com",
            "creator_name": "Northline Studio",
            "amount_cents": 2400,
            "currency": "USD",
            "payment_state": state,
            "assets": [
                {
                    "title": "Field Notes PDF",
                    "download_url": "https://downloads.example.com/field-notes",
                },
                {
                    "title": "Cover Pack",
                    "download_url": "https://downloads.example.com/cover-pack",
                },
            ],
            "subscriber_update": {
                "list_name": "studio notes",
                "state": "subscribed",
            },
        }
    )


def test_paid_order_delivers_assets_and_records_subscriber_state() -> None:
    email = RecordingEmail()

    result = send_paid_order_receipt(order(), email)

    assert result.message_id == "msg_receipt_1042"
    assert result.delivered_asset_count == 2
    assert result.subscriber_state == "subscribed"
    assert email.call is not None
    assert "Field Notes PDF" in email.call["html"]
    assert "You are subscribed to studio notes updates." in email.call["html"]
    assert email.call["idempotency_key"] == "creator-receipt-ORDER-1042"


def test_pending_order_never_sends_a_receipt() -> None:
    email = RecordingEmail()

    with pytest.raises(ValueError, match="only after payment"):
        send_paid_order_receipt(order("pending"), email)

    assert email.call is None

