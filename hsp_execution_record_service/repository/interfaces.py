from typing import Protocol

from hsp_execution_record_service.domain.models import ExecutionRecord


class ExecutionRecordRepository(Protocol):
    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        ...

    async def get_by_id(self, record_id: str) -> ExecutionRecord | None:
        ...

    async def get_by_order_id(self, order_id: str) -> ExecutionRecord | None:
        ...

    async def update(self, record: ExecutionRecord) -> ExecutionRecord:
        ...

    async def list_all(self) -> list[ExecutionRecord]:
        ...

    async def list_by_worker(self, worker_id: str) -> list[ExecutionRecord]:
        ...
