from fastapi import APIRouter

from app.analysis.engine import AnalysisEngine
from app.schemas.analysis import AnalysisRequest, AnalysisSummary

router = APIRouter(tags=["analysis"])


@router.post("/analysis", response_model=AnalysisSummary)
def analyze_wafer(request: AnalysisRequest) -> AnalysisSummary:
    return AnalysisEngine().analyze(
        request.dataset,
        config=request.config,
    )
