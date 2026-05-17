from hsp_execution_record_service.domain.models import ExecutionRecord
from rpc.echo.v1 import echo_pb2


def to_grpc_record(record: ExecutionRecord) -> echo_pb2.ExecutionRecord:
    return echo_pb2.ExecutionRecord(
        id=record.id,
        order_id=record.order_id,
        worker_id=record.worker_id,
        status=record.status.value,
        start_time=record.start_time.isoformat(),
        end_time=record.end_time.isoformat() if record.end_time is not None else "",
        duration_minutes=record.duration_minutes or 0,
        created_at=record.created_at.isoformat(),
        updated_at=record.updated_at.isoformat(),
    )
