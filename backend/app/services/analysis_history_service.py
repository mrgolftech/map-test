import json
from datetime import UTC, datetime
from uuid import uuid4

from pydantic import TypeAdapter
from sqlalchemy.orm import Session

from app.analysis.engine import AnalysisEngine
from app.core.errors import AppError
from app.db.models import AnalysisRecord
from app.repositories.analysis_repository import AnalysisRepository
from app.schemas.ai import AIReport
from app.schemas.analysis import AnalysisSummary
from app.schemas.history import (
    AnalysisCreateRequest,
    AnalysisDetail,
    AnalysisListItem,
)
from app.schemas.parsing import (
    ParseStatus,
    SourceDescriptor,
    ValidationIssue,
    ValidationSeverity,
)
from app.schemas.wafer import WaferDataset
from app.validation.canonical import validate_dataset

_source_adapter = TypeAdapter(list[SourceDescriptor])
_validation_adapter = TypeAdapter(list[ValidationIssue])


class AnalysisHistoryService:
    def __init__(self, session: Session) -> None:
        self._repository = AnalysisRepository(session)

    def create(self, request: AnalysisCreateRequest) -> AnalysisDetail:
        canonical_issues = validate_dataset(request.dataset)
        errors = [
            issue
            for issue in [*request.validation_issues, *canonical_issues]
            if issue.severity == ValidationSeverity.ERROR
        ]
        if errors:
            raise AppError(
                code="ANALYSIS_DATASET_INVALID",
                message="WaferDataset failed validation and cannot be persisted.",
                status_code=422,
                details={
                    "issues": [issue.model_dump(mode="json") for issue in errors],
                },
            )

        analysis = AnalysisEngine().analyze(request.dataset)
        all_issues = [*request.validation_issues, *canonical_issues]
        status = (
            ParseStatus.WARNING
            if any(
                issue.severity == ValidationSeverity.WARNING
                for issue in all_issues
            )
            else ParseStatus.VALID
        )

        main_fail_bin = self._main_fail_bin(request.dataset)
        main_pattern = analysis.patterns[0].pattern if analysis.patterns else None

        metadata = request.dataset.metadata
        summary = request.dataset.summary
        record = AnalysisRecord(
            id=str(uuid4()),
            product_id=metadata.product_id,
            lot_id=metadata.lot_id,
            wafer_id=metadata.wafer_id,
            flow_id=metadata.flow_id,
            yield_value=summary.yield_,
            tested_die=summary.tested_die,
            pass_die=summary.pass_die,
            fail_die=summary.fail_die,
            main_fail_bin=main_fail_bin,
            main_pattern=main_pattern,
            validation_status=status.value,
            dataset_json=request.dataset.model_dump_json(by_alias=True),
            analysis_summary_json=analysis.model_dump_json(by_alias=True),
            sources_json=json.dumps(
                [
                    source.model_dump(mode="json")
                    for source in request.sources
                ],
                separators=(",", ":"),
            ),
            validation_json=json.dumps(
                [
                    issue.model_dump(mode="json")
                    for issue in all_issues
                ],
                separators=(",", ":"),
            ),
        )
        return self._to_detail(self._repository.add(record))

    def get(self, analysis_id: str) -> AnalysisDetail:
        record = self._repository.get(analysis_id)
        if record is None:
            raise AppError(
                code="ANALYSIS_NOT_FOUND",
                message="Analysis record was not found.",
                status_code=404,
                details={"analysis_id": analysis_id},
            )
        return self._to_detail(record)

    def save_ai_report(
        self,
        analysis_id: str,
        *,
        model: str,
        report: AIReport,
    ) -> AnalysisDetail:
        record = self._repository.get(analysis_id)
        if record is None:
            raise AppError(
                code="ANALYSIS_NOT_FOUND",
                message="Analysis record was not found.",
                status_code=404,
                details={"analysis_id": analysis_id},
            )
        record.ai_report_json = report.model_dump_json()
        record.ai_model = model
        record.ai_generated_at = datetime.now(UTC)
        return self._to_detail(self._repository.save(record))

    def delete(self, analysis_id: str) -> None:
        record = self._repository.get(analysis_id)
        if record is None:
            raise AppError(
                code="ANALYSIS_NOT_FOUND",
                message="Analysis record was not found.",
                status_code=404,
                details={"analysis_id": analysis_id},
            )
        self._repository.delete(record)

    def list(
        self,
        *,
        product_id: str | None,
        lot_id: str | None,
        wafer_id: str | None,
        created_from: datetime | None,
        created_to: datetime | None,
        yield_min: float | None,
        yield_max: float | None,
        main_fail_bin: int | None,
        pattern: str | None,
        page: int,
        page_size: int,
    ) -> tuple[list[AnalysisListItem], int]:
        records, total = self._repository.list(
            product_id=product_id,
            lot_id=lot_id,
            wafer_id=wafer_id,
            created_from=created_from,
            created_to=created_to,
            yield_min=yield_min,
            yield_max=yield_max,
            main_fail_bin=main_fail_bin,
            pattern=pattern,
            page=page,
            page_size=page_size,
        )
        return [self._to_list_item(record) for record in records], total

    @staticmethod
    def _main_fail_bin(dataset: WaferDataset) -> int | None:
        described_pass = {
            item.bin
            for item in dataset.bins
            if "PASS" in (item.description or "").upper()
        }
        pass_bins = described_pass or {1}
        fail_bins = [
            item
            for item in dataset.bins
            if item.bin not in pass_bins and item.count > 0
        ]
        if not fail_bins:
            return None
        return max(fail_bins, key=lambda item: item.count).bin

    @staticmethod
    def _to_list_item(record: AnalysisRecord) -> AnalysisListItem:
        return AnalysisListItem(
            id=record.id,
            created_at=record.created_at,
            product_id=record.product_id,
            lot_id=record.lot_id,
            wafer_id=record.wafer_id,
            flow_id=record.flow_id,
            yield_=record.yield_value,
            tested_die=record.tested_die,
            pass_die=record.pass_die,
            fail_die=record.fail_die,
            main_fail_bin=record.main_fail_bin,
            main_pattern=record.main_pattern,
            validation_status=record.validation_status,
        )

    @classmethod
    def _to_detail(cls, record: AnalysisRecord) -> AnalysisDetail:
        return AnalysisDetail(
            **cls._to_list_item(record).model_dump(by_alias=True),
            dataset=WaferDataset.model_validate_json(record.dataset_json),
            analysis=AnalysisSummary.model_validate_json(
                record.analysis_summary_json
            ),
            sources=_source_adapter.validate_json(record.sources_json),
            validation_issues=_validation_adapter.validate_json(
                record.validation_json
            ),
            ai_report=(
                AIReport.model_validate_json(record.ai_report_json)
                if record.ai_report_json
                else None
            ),
            ai_model=record.ai_model,
            ai_generated_at=record.ai_generated_at,
        )
