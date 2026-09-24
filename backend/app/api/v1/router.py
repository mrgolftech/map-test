from fastapi import APIRouter, Depends

from app.api.v1.ai import router as ai_router
from app.api.v1.analyses import router as analyses_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.auth import router as auth_router
from app.api.v1.comparison import router as comparison_router
from app.api.v1.dashboard import router as dashboard_router
from app.api.v1.files import router as files_router
from app.api.v1.health import router as health_router
from app.api.v1.simulator import router as simulator_router
from app.api.v1.version import router as version_router
from app.core.auth import require_admin

api_router = APIRouter()
api_router.include_router(health_router)
api_router.include_router(version_router)
api_router.include_router(auth_router)

protected_router = APIRouter(dependencies=[Depends(require_admin)])
protected_router.include_router(dashboard_router)
protected_router.include_router(ai_router)
protected_router.include_router(files_router)
protected_router.include_router(simulator_router)
protected_router.include_router(analysis_router)
protected_router.include_router(analyses_router)
protected_router.include_router(comparison_router)

api_router.include_router(protected_router)
