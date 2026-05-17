from hsp_execution_record_service.domain.models import ExecutionRecord
from hsp_execution_record_service.transport.http.schemas import ExecutionRecordResponse


def to_http_response(record: ExecutionRecord) -> ExecutionRecordResponse:
    return ExecutionRecordResponse(
        id=record.id,
        order_id=record.order_id,
        worker_id=record.worker_id,
        status=record.status.value,
        start_time=record.start_time.isoformat(),
        end_time=record.end_time.isoformat() if record.end_time is not None else None,
        duration_minutes=record.duration_minutes,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat(),
    )
