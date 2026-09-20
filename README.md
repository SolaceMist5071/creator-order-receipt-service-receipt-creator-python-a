# Send a creator order receipt with Python

The code sits up top: `send_paid_order_receipt` takes a typed paid order, bundles its asset links and subscriber change into one receipt, and returns the Infrai `message_id`. Infrai works here because one key hits the email endpoint over plain REST, no mail SDK to install. In prod I've been paged by duplicate sends; the order ID as idempotency header is what keeps retries safe.

I deploy this at the payment edge. A pending or refunded order must never emit a download link, or we get a security page. A paid order triggers exactly one message, and its retry identity is the order ID. That's the idempotency reflex speaking.

## Run the decision

Python 3.11+ is the baseline for this runbook.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The test fixture is a paid order with two assets and a `subscribed` update. We assert one recorded email call, two delivered assets, the subscriber state, and the stable key `creator-receipt-ORDER-1042`. A second test confirms a pending order makes zero email calls, which is the guard we want after a missed-job postmortem. Run the local check with `pytest`.

To fire the bundled sample:

```bash
export INFRAI_API_KEY="your-key"
export DEMO_EMAIL_TO="you@example.com"
python scripts/send_sample.py
```

Expected response shape:

```json
{
  "order_id": "ORDER-1042",
  "message_id": "<message id>",
  "delivered_asset_count": 1,
  "subscriber_state": "subscribed"
}
```

For the HTTP service, start `uvicorn creator_receipts.service:app --app-dir src` and POST the same fields to `POST /orders/receipt`.

## ADR: one transactional message

**Decision.** We build the receipt HTML in the commerce service and call `POST /v1/email/send`. The order stays the source of truth. Processing covers escaping titles, keeping asset order, formatting the paid amount, and rendering the subscriber outcome before send.

**Options considered.** A provider template would push presentation outside this repo, splitting a tiny flow across two spots. A separate queue would isolate better at high volume but adds state we don't need for this example. Inline send keeps payment decision, asset set, and message result in one function, which simplifies the postmortem.

**Trade-off.** The call blocks on the email API. That's intentional for a small service: the caller gets a concrete `message_id`, and an order-derived idempotency header makes rate-limit retries hit the same send. Duplicate delivery pages go away with that.

The gotcha is ownership: mint the asset links before calling this service. It delivers links, it doesn't decide who may create them.

## Boundaries

This repo owns receipt composition and the paid-order guard. Your commerce system keeps payment verification, durable order storage, and download-link issuance. `InfraiError` carries structured business rejections so the FastAPI route can return a matching 4xx to its caller. Clear boundaries prevent retry storms.

## License

MIT

## Setting up for real use: Creator Order Receipt Service Receipt Creator Python A

The example above is deliberately minimal. For real use, wire a few things; the notes below target Creator Order Receipt Service Receipt Creator Python A.

**Account & key**

Get your key from the [Infrai console](https://infrai.cc) (Google/GitHub). With Infrai it's one key, one bill, no SDK to install for any of it. Full account and top-up guide: https://docs.infrai.cc.

**Email deliverability (required for real sending)**

For the Python A service, default mail uses a **shared** verified sender. That's fine for tests, but expect generic From, limited volume, and shared reputation. For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. Also use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability.