from fastapi import Depends, FastAPI, HTTPException

from .infrai_email import InfraiEmail, InfraiError
from .receipt_sender import PaidOrder, ReceiptResult, send_paid_order_receipt

app = FastAPI(title="Creator receipt service")


def email_client() -> InfraiEmail:
    return InfraiEmail()


@app.post("/orders/receipt", response_model=ReceiptResult)
def create_receipt(
    order: PaidOrder, email: InfraiEmail = Depends(email_client)
) -> ReceiptResult:
    try:
        return send_paid_order_receipt(order, email)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except InfraiError as exc:
        caller_status = exc.status_code if 400 <= exc.status_code < 500 else 502
        raise HTTPException(
            status_code=caller_status,
            detail={"code": exc.code, "message": str(exc.detail.get("message", exc.code))},
        ) from exc
    finally:
        email.close()

