from fastapi import APIRouter

from app.api.v1.analyses import router as analyses_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.files import router as files_router
from app.api.v1.health import router as health_router
from app.api.v1.version import router as version_router

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(version_router)
api_router.include_router(files_router)
api_router.include_router(analysis_router)
api_router.include_router(analyses_router)
api_router.include_router(comparison_router)
