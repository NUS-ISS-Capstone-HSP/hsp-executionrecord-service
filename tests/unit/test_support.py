from datetime import UTC, datetime

from hsp_execution_record_service.domain.models import ExecutionRecord, RecordStatus


def build_execution_record(id: str, order_id: str, worker_id: str) -> ExecutionRecord:
    now = datetime.now(UTC)
    return ExecutionRecord(
        id=id,
        order_id=order_id,
        worker_id=worker_id,
        status=RecordStatus.STARTED,
        start_time=now,
        end_time=None,
        duration_minutes=None,
        created_at=now,
        updated_at=now,
    )
