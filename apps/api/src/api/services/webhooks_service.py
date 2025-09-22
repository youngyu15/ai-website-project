from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from api.repositories import webhooks_repo as repo

async def emit_prediction_event(db: AsyncSession, *, owner_id: UUID, prediction_id: UUID, event: str):
    # Lookup user webhooks and log a fake delivery (no HTTP calls yet)
    hooks = await repo.list_webhooks(db, owner_id=owner_id)
    for wh in hooks:
        await repo.log_delivery(db, webhook_id=wh.id, prediction_id=prediction_id, status="delivered", attempts=1, last_error=None)