from hsp_execution_record_service.domain.models import ExecutionRecord
from hsp_execution_record_service.repository.interfaces import ExecutionRecordRepository


class InMemoryExecutionRecordRepository(ExecutionRecordRepository):
    def __init__(self) -> None:
        self._store: dict[str, ExecutionRecord] = {}

    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        self._store[record.id] = record
        return record

    async def get_by_id(self, record_id: str) -> ExecutionRecord | None:
        return self._store.get(record_id)

    async def get_by_order_id(self, order_id: str) -> ExecutionRecord | None:
        for record in self._store.values():
            if record.order_id == order_id:
                return record
        return None

    async def update(self, record: ExecutionRecord) -> ExecutionRecord:
        self._store[record.id] = record
        return record

    async def list_all(self) -> list[ExecutionRecord]:
        return sorted(self._store.values(), key=lambda record: record.created_at)

    async def list_by_worker(self, worker_id: str) -> list[ExecutionRecord]:
        records = [record for record in self._store.values() if record.worker_id == worker_id]
        return sorted(records, key=lambda record: record.created_at)
