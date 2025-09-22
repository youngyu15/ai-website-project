from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.deps import get_current_user
from app.schemas import WebhookCreateRequest, WebhookOut
from app.repositories.webhooks import create_webhook, list_webhooks
from app.core.security import hash_password
from app.db.engine import get_session

router = APIRouter()

@router.post("/endpoints", response_model=WebhookOut, status_code=201)
async def create_webhook_endpoint(body: WebhookCreateRequest, user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    secret_hash = hash_password(body.secret) if body.secret else None
    wh = await create_webhook(db, owner_id=user.id, url=body.url, events=body.events, secret_hash=secret_hash)
    return WebhookOut.model_validate(wh, from_attributes=True)

@router.get("/endpoints", response_model=list[WebhookOut])
async def list_webhook_endpoints(user = Depends(get_current_user), db: AsyncSession = Depends(get_session)):
    hooks = await list_webhooks(db, owner_id=user.id)
    return [WebhookOut.model_validate(h, from_attributes=True) for h in hooks]