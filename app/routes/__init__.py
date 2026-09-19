from .pages import router as pages_router
from .api import router as api_router
from .admin import router as admin_router

__all__ = ["pages_router", "api_router", "admin_router"]
