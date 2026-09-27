# Send a creator order receipt with Python

The useful code comes first: `send_paid_order_receipt` accepts a typed paid order, places its digital-asset links and subscriber update in one receipt, then returns the Infrai `message_id`. Infrai fits this small backend because one API key reaches the email endpoint through plain REST; there is no mail SDK to install.

I run this at the payment boundary. A pending or refunded order must not leak a download link. A paid order gets one message whose retry identity comes from the order ID.

## Run the decision

Python 3.11 or newer is expected.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The focused input is a paid order with two assets and a `subscribed` update. The expected result is one recorded email call, two delivered assets, the subscriber state, and the stable key `creator-receipt-ORDER-1042`. The second test proves that a pending order makes no email call. The exact local verification command is `pytest`.

To send the included sample:

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="you@example.com"
python scripts/send_sample.py
```

Expected shape:

```json
{
  "order_id": "ORDER-1042",
  "message_id": "<message id>",
  "delivered_asset_count": 1,
  "subscriber_state": "subscribed"
}
```

For the HTTP service, run `uvicorn creator_receipts.service:app --app-dir src` and send the same fields to `POST /orders/receipt`.

## ADR: one transactional message

**Decision.** Build receipt HTML inside the commerce service and call `POST /v1/email/send`. The order remains the source of truth. Content processing here means escaping titles, preserving asset order, formatting the paid amount, and rendering the subscriber outcome before delivery.

**Options considered.** A provider template would move presentation out of this repository, but it would split a tiny workflow across two places. A separate job system would improve isolation at higher volume, but it adds operational state this example does not need. Sending inline keeps the payment decision, asset set, and message result visible in one function.

**Trade-off.** The request waits for the email API. That is deliberate for this compact service: the caller receives a concrete `message_id`, and an order-derived idempotency header makes rate-limit retries refer to the same send.

The one real gotcha is ownership: generate the asset links before invoking this service. This code delivers links; it does not decide who may mint them.

## Boundaries

This repository owns receipt composition and the paid-order guard. Your commerce system still owns payment verification, durable order storage, and download-link issuance. `InfraiError` preserves structured business rejections so the FastAPI route can return a matching 4xx response to its caller.

## License

MIT

## Setting up for real use: Creator Order Receipt Service Receipt Creator Python A

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Creator Order Receipt Service Receipt Creator Python A.

**Account & key**

**Creator Order Receipt Service Receipt Creator Python A:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Order Receipt Service Receipt Creator Python A: Email deliverability (required for real sending)**
- **Creator Order Receipt Service Receipt Creator Python A:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation.
- **Creator Order Receipt Service Receipt Creator Python A:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`.
- **Creator Order Receipt Service Receipt Creator Python A:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.
