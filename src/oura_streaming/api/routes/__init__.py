"""API route modules."""

from fastapi import APIRouter

from .auth import router as auth_router
from .dashboard import router as dashboard_router
from .health import router as health_router
from .subscriptions import router as subscriptions_router
from .webhooks import router as webhooks_router

api_router = APIRouter()
api_router.include_router(health_router, tags=["health"])
api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
api_router.include_router(webhooks_router, tags=["webhooks"])
api_router.include_router(subscriptions_router, tags=["subscriptions"])
api_router.include_router(dashboard_router, tags=["dashboard"])

__all__ = ["api_router"]
