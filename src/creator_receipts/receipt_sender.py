from __future__ import annotations

from html import escape
from typing import Literal, Protocol

from pydantic import BaseModel, Field, HttpUrl


class DigitalAsset(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    download_url: HttpUrl


class SubscriberUpdate(BaseModel):
    list_name: str = Field(min_length=1, max_length=80)
    state: Literal["subscribed", "unchanged"]


class PaidOrder(BaseModel):
    order_id: str = Field(min_length=1, max_length=80)
    buyer_email: str = Field(pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
    creator_name: str = Field(min_length=1, max_length=80)
    amount_cents: int = Field(ge=0)
    currency: str = Field(pattern=r"^[A-Z]{3}$")
    payment_state: Literal["paid", "pending", "refunded"]
    assets: list[DigitalAsset] = Field(min_length=1)
    subscriber_update: SubscriberUpdate


class ReceiptResult(BaseModel):
    order_id: str
    message_id: str
    delivered_asset_count: int
    subscriber_state: Literal["subscribed", "unchanged"]


class EmailSender(Protocol):
    def send(
        self, *, to: str, subject: str, html: str, idempotency_key: str
    ) -> str:
        raise AssertionError("Protocol method")


def send_paid_order_receipt(order: PaidOrder, email: EmailSender) -> ReceiptResult:
    if order.payment_state != "paid":
        raise ValueError("A receipt is sent only after payment is paid")

    amount = f"{order.amount_cents / 100:.2f} {order.currency}"
    links = "".join(
        f'<li><a href="{escape(str(asset.download_url), quote=True)}">'
        f"{escape(asset.title)}</a></li>"
        for asset in order.assets
    )
    subscriber_line = (
        f"You are subscribed to {escape(order.subscriber_update.list_name)} updates."
        if order.subscriber_update.state == "subscribed"
        else f"Your {escape(order.subscriber_update.list_name)} update preference is unchanged."
    )
    html = (
        f"<h1>Receipt from {escape(order.creator_name)}</h1>"
        f"<p>Order {escape(order.order_id)}: {amount}</p>"
        f"<h2>Your downloads</h2><ul>{links}</ul>"
        f"<p>{subscriber_line}</p>"
    )
    message_id = email.send(
        to=str(order.buyer_email),
        subject=f"Your {order.creator_name} receipt ({order.order_id})",
        html=html,
        idempotency_key=f"creator-receipt-{order.order_id}",
    )
    return ReceiptResult(
        order_id=order.order_id,
        message_id=message_id,
        delivered_asset_count=len(order.assets),
        subscriber_state=order.subscriber_update.state,
    )
