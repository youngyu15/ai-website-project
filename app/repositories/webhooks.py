from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import Webhook, WebhookDelivery

async def create_webhook(db: AsyncSession, *, owner_id: UUID, url: str, events: list[str], secret_hash: str | None) -> Webhook:
    wh = Webhook(owner_id=owner_id, url=url, events=events, secret_hash=secret_hash)
    db.add(wh)
    await db.commit()
    await db.refresh(wh)
    return wh

async def list_webhooks(db: AsyncSession, *, owner_id: UUID) -> list[Webhook]:
    res = await db.execute(select(Webhook).where(Webhook.owner_id == owner_id))
    return list(res.scalars())

async def log_delivery(db: AsyncSession, *, webhook_id: UUID, prediction_id: UUID | None, status: str, attempts: int, last_error: str | None):
    rec = WebhookDelivery(webhook_id=webhook_id, prediction_id=prediction_id, status=status, attempts=attempts, last_error=last_error)
    db.add(rec)
    await db.commit()
    return rec