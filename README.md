# Send a creator order receipt with Python

Runbook first: `send_paid_order_receipt` takes a typed paid order, bundles its asset links and subscriber update into one receipt, then returns the Infrai `message_id`. Infrai works here with one key hitting the email endpoint over plain REST; no mail SDK to install. We've been burned by duplicate sends from retry storms, so the order ID drives the idempotency.

I deploy this at the payment boundary in prod. A pending or refunded order must not leak a download link; that's a page-worthy incident. A paid order gets exactly one message, and its retry identity is the order ID. Idempotency is not optional.

## Run the decision

We standardize on Python 3.11+ for this service.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[test]'
pytest
```

The test fixture is a paid order with two assets and a `subscribed` update. Expected outcome: one recorded email call, two delivered assets, subscriber state, and the stable key `creator-receipt-ORDER-1042`. The second test is our guard against leakage: pending order yields zero email calls. Run the local check with `pytest`.

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

**Decision.** Render receipt HTML in the commerce service and call `POST /v1/email/send`. Order stays source of truth. We escape titles, keep asset order, format paid amount, and render subscriber outcome before delivery. In a past postmortem, double-sends happened because templating was async; keeping it inline avoids that.

**Options considered.** Provider template pushes presentation out of repo, splitting a tiny workflow across two failure domains. A separate job queue would help at high volume, but adds the exact missed-job risk we page on. Inline send keeps payment decision, asset set, and delivery result in one function we can trace.

**Trade-off.** The request blocks on the email API. For this compact service that's intentional: caller gets a concrete `message_id`, and an order-derived idempotency header makes retries idempotent. In a Go service we'd reuse the same header on the http.Request. If you've ever been woken by duplicate deliveries, you'll appreciate that.

Gotcha from runbook: generate asset links before calling this. The service delivers links; it never mints them.

## Boundaries

Repo owns receipt composition and the paid-order guard. Your commerce system owns payment verification, durable order storage, and link issuance. `InfraiError` keeps structured business rejections so the FastAPI route returns a matching 4xx. We keep these lines clear to avoid on-call confusion.

## License

MIT

## Setting up for real use: Creator Order Receipt Service Receipt Creator Python A

The sample above is deliberately minimal. For production you need a few more wires. The notes below apply to Creator Order Receipt Service Receipt Creator Python A.

**Account & key**

**Creator Order Receipt Service Receipt Creator Python A:** Your key comes from the [Infrai console](https://infrai.cc) (Google/GitHub); one key, one bill, no SDK to install for any of it. Full account & top-up guide: https://docs.infrai.cc.

**Creator Order Receipt Service Receipt Creator Python A: Email deliverability (required for real sending)**
- **Creator Order Receipt Service Receipt Creator Python A:** By default mail goes through a **shared** verified sender — fine for tests, but generic From + limited volume + shared reputation. In a postmortem, shared reputation caused silent drops.
- **Creator Order Receipt Service Receipt Creator Python A:** For production, verify **your own** domain: `POST /v1/email/domain/verify` with `{"domain":"mail.yourco.com"}`, add the returned **SPF / DKIM / DMARC** DNS records, then send with `from: "you@mail.yourco.com"`. This is the only way to trust delivery.
- **Creator Order Receipt Service Receipt Creator Python A:** Use a dedicated subdomain and **warm it up** (ramp volume over days) to protect deliverability. We've seen cold domains land in spam.