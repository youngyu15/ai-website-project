from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.settings import settings
from api.routers import auth_router, users_router, uploads_router, predictions_router, shares_router, webhooks_router

app = FastAPI(title=settings.app_name, version="1.0.0")

@app.get("/health")
def health():
    return {"status": True}

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router.router, prefix="/v1/auth", tags=["auth"])
app.include_router(users_router.router, prefix="/v1/users", tags=["users"])
app.include_router(uploads_router.router, prefix="/v1/uploads", tags=["uploads"])
app.include_router(predictions_router.router, prefix="/v1/predictions", tags=["predictions"])
app.include_router(shares_router.router, prefix="/v1/shares", tags=["shares"])
app.include_router(webhooks_router.router, prefix="/v1/webhooks", tags=["webhooks"])