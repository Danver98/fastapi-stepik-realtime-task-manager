"""
    Endpoints for health check
"""

from fastapi import APIRouter

check_router = APIRouter(
    prefix="/checks",
    tags=["checks"]
)


@check_router.get("/health")
async def health_check():
    """Health check test endpoint"""
    return {"status": "ok"}
