from fastapi import APIRouter

from app.analysis.engine import AnalysisEngine
from app.core.errors import AppError
from app.schemas.analysis import AnalysisRequest, AnalysisSummary
from app.schemas.parsing import ValidationSeverity
from app.validation.canonical import validate_dataset

router = APIRouter(tags=["analysis"])


@router.post("/analysis", response_model=AnalysisSummary)
def analyze_wafer(request: AnalysisRequest) -> AnalysisSummary:
    issues = validate_dataset(request.dataset)
    errors = [
        issue
        for issue in issues
        if issue.severity == ValidationSeverity.ERROR
    ]
    if errors:
        raise AppError(
            code="ANALYSIS_DATASET_INVALID",
            message="WaferDataset failed canonical validation.",
            status_code=422,
            details={
                "issues": [
                    issue.model_dump(mode="json")
                    for issue in errors
                ]
            },
        )

    return AnalysisEngine().analyze(
        request.dataset,
        config=request.config,
    )
