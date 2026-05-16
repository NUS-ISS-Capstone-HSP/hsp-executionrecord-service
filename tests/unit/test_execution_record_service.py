import pytest

from hsp_execution_record_service.domain.errors import ConflictError, ForbiddenError
from hsp_execution_record_service.domain.models import RecordStatus
from hsp_execution_record_service.repository.in_memory import InMemoryExecutionRecordRepository
from hsp_execution_record_service.service.execution_record_service import (
    ExecutionRecordService,
    parse_actor,
)


class DeniedAssignmentClient:
    async def is_order_assigned_to_worker(self, order_id: str, worker_id: str) -> bool:
        del order_id, worker_id
        return False


@pytest.mark.asyncio
async def test_start_service_success() -> None:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())

    record = await service.start_service(
        " order-1 ",
        " worker-1 ",
        parse_actor("worker-1", "worker"),
    )

    assert record.order_id == "order-1"
    assert record.worker_id == "worker-1"
    assert record.status == RecordStatus.STARTED
    assert record.start_time is not None
    assert record.end_time is None
    assert record.duration_minutes is None


@pytest.mark.asyncio
async def test_start_service_rejects_other_worker() -> None:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())

    with pytest.raises(ForbiddenError):
        await service.start_service("order-1", "worker-2", parse_actor("worker-1", "worker"))


@pytest.mark.asyncio
async def test_start_service_rejects_unassigned_order() -> None:
    service = ExecutionRecordService(
        InMemoryExecutionRecordRepository(),
        order_assignment_client=DeniedAssignmentClient(),
    )

    with pytest.raises(ForbiddenError):
        await service.start_service("order-1", "worker-1", parse_actor("worker-1", "worker"))


@pytest.mark.asyncio
async def test_start_service_rejects_duplicate_start() -> None:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())
    actor = parse_actor("worker-1", "worker")

    await service.start_service("order-1", "worker-1", actor)

    with pytest.raises(ConflictError):
        await service.start_service("order-1", "worker-1", actor)


@pytest.mark.asyncio
async def test_end_service_success_and_rejects_duplicate_end() -> None:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())
    actor = parse_actor("worker-1", "worker")
    started = await service.start_service("order-1", "worker-1", actor)

    completed = await service.end_service(started.id, actor)

    assert completed.status == RecordStatus.COMPLETED
    assert completed.end_time is not None
    assert completed.duration_minutes is not None

    with pytest.raises(ConflictError):
        await service.end_service(started.id, actor)


@pytest.mark.asyncio
async def test_query_service_records_enforces_worker_scope() -> None:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())
    worker_1 = parse_actor("worker-1", "worker")
    worker_2 = parse_actor("worker-2", "worker")
    admin = parse_actor("admin-1", "admin")

    await service.start_service("order-1", "worker-1", worker_1)
    await service.start_service("order-2", "worker-2", worker_2)

    worker_records = await service.query_service_records(worker_1)
    admin_records = await service.query_service_records(admin)

    assert [record.worker_id for record in worker_records] == ["worker-1"]
    assert {record.worker_id for record in admin_records} == {"worker-1", "worker-2"}

    with pytest.raises(ForbiddenError):
        await service.query_service_records(worker_1, worker_id="worker-2")
