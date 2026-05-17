from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from hsp_execution_record_service.domain.models import ExecutionRecord, RecordStatus
from hsp_execution_record_service.infrastructure.orm import ExecutionRecordORM
from hsp_execution_record_service.repository.interfaces import ExecutionRecordRepository


class SQLAlchemyExecutionRecordRepository(ExecutionRecordRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession]) -> None:
        self._session_factory = session_factory

    async def create(self, record: ExecutionRecord) -> ExecutionRecord:
        row = ExecutionRecordORM(
            id=record.id,
            order_id=record.order_id,
            worker_id=record.worker_id,
            status=record.status.value,
            start_time=record.start_time,
            end_time=record.end_time,
            duration_minutes=record.duration_minutes,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        async with self._session_factory() as session:
            session.add(row)
            await session.commit()
            await session.refresh(row)
        return _to_domain(row)

    async def get_by_id(self, record_id: str) -> ExecutionRecord | None:
        async with self._session_factory() as session:
            stmt = select(ExecutionRecordORM).where(ExecutionRecordORM.id == record_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_domain(row)

    async def get_by_order_id(self, order_id: str) -> ExecutionRecord | None:
        async with self._session_factory() as session:
            stmt = select(ExecutionRecordORM).where(ExecutionRecordORM.order_id == order_id)
            result = await session.execute(stmt)
            row = result.scalar_one_or_none()
        if row is None:
            return None
        return _to_domain(row)

    async def update(self, record: ExecutionRecord) -> ExecutionRecord:
        async with self._session_factory() as session:
            row = await session.get(ExecutionRecordORM, record.id)
            if row is None:
                raise ValueError(f"execution record '{record.id}' not found")

            row.order_id = record.order_id
            row.worker_id = record.worker_id
            row.status = record.status.value
            row.start_time = record.start_time
            row.end_time = record.end_time
            row.duration_minutes = record.duration_minutes
            row.created_at = record.created_at
            row.updated_at = record.updated_at

            await session.commit()
            await session.refresh(row)
        return _to_domain(row)

    async def list_all(self) -> list[ExecutionRecord]:
        async with self._session_factory() as session:
            stmt = select(ExecutionRecordORM).order_by(ExecutionRecordORM.created_at)
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [_to_domain(row) for row in rows]

    async def list_by_worker(self, worker_id: str) -> list[ExecutionRecord]:
        async with self._session_factory() as session:
            stmt = (
                select(ExecutionRecordORM)
                .where(ExecutionRecordORM.worker_id == worker_id)
                .order_by(ExecutionRecordORM.created_at)
            )
            result = await session.execute(stmt)
            rows = result.scalars().all()
        return [_to_domain(row) for row in rows]


def _to_domain(row: ExecutionRecordORM) -> ExecutionRecord:
    return ExecutionRecord(
        id=row.id,
        order_id=row.order_id,
        worker_id=row.worker_id,
        status=RecordStatus(row.status),
        start_time=_ensure_utc(row.start_time),
        end_time=_ensure_utc(row.end_time) if row.end_time is not None else None,
        duration_minutes=row.duration_minutes,
        created_at=_ensure_utc(row.created_at),
        updated_at=_ensure_utc(row.updated_at),
    )


def _ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value
