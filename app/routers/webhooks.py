# app/routers/webhooks.py
from fastapi import APIRouter, Depends, status
from uuid import uuid4
from app.deps import get_current_user
from app.schemas import WebhookCreateRequest, WebhookBase
from app.store import webhooks, now

router = APIRouter()

@router.post("/endpoints", response_model=WebhookBase, status_code=status.HTTP_201_CREATED)
def create_webhook(body: WebhookCreateRequest, user=Depends(get_current_user)):
    wid = f"wh_{uuid4().hex}"
    webhooks[wid] = {
        "id": wid,
        "url": body.url,
        "events": body.events,
        "created_at": now(),
        "owner_id": user.id,
    }
    return WebhookBase(**{k: v for k, v in webhooks[wid].items() if k != "owner_id"})

@router.get("/endpoints", response_model=list[WebhookBase])
def list_webhooks(user=Depends(get_current_user)):
    res = []
    for wh in webhooks.values():
        if wh["owner_id"] == user.id:
            res.append(WebhookBase(**{k: v for k, v in wh.items() if k != "owner_id"}))
    return res