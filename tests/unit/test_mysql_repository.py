from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from hsp_execution_record_service.domain.models import RecordStatus
from hsp_execution_record_service.infrastructure.db import (
    create_engine,
    create_session_factory,
    init_db,
)
from hsp_execution_record_service.repository.mysql import (
    SQLAlchemyExecutionRecordRepository,
    _ensure_utc,
)
from tests.unit.test_support import build_execution_record


@pytest.mark.asyncio
async def test_sqlalchemy_repository_create_and_get(tmp_path: Path) -> None:
    db_file = tmp_path / "execution_record.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyExecutionRecordRepository(create_session_factory(engine))

    record = build_execution_record(id=str(uuid4()), order_id="order-1", worker_id="worker-1")
    created = await repository.create(record)
    fetched = await repository.get_by_id(created.id)

    assert created.order_id == "order-1"
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.status == RecordStatus.STARTED

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_by_order_id(tmp_path: Path) -> None:
    db_file = tmp_path / "execution_record.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyExecutionRecordRepository(create_session_factory(engine))
    record = build_execution_record(id=str(uuid4()), order_id="order-1", worker_id="worker-1")
    await repository.create(record)

    fetched = await repository.get_by_order_id("order-1")
    missing = await repository.get_by_order_id("missing-order")

    assert fetched is not None
    assert fetched.id == record.id
    assert missing is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_get_missing_returns_none(tmp_path: Path) -> None:
    db_file = tmp_path / "execution_record.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyExecutionRecordRepository(create_session_factory(engine))

    fetched = await repository.get_by_id("missing-id")
    assert fetched is None

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_update_and_list(tmp_path: Path) -> None:
    db_file = tmp_path / "execution_record.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyExecutionRecordRepository(create_session_factory(engine))
    record = build_execution_record(id=str(uuid4()), order_id="order-1", worker_id="worker-1")
    created = await repository.create(record)
    created.status = RecordStatus.COMPLETED
    created.end_time = datetime.now(UTC)
    created.duration_minutes = 15
    updated = await repository.update(created)
    worker_records = await repository.list_by_worker("worker-1")
    all_records = await repository.list_all()

    assert updated.status == RecordStatus.COMPLETED
    assert updated.duration_minutes == 15
    assert [record.id for record in worker_records] == [created.id]
    assert [record.id for record in all_records] == [created.id]

    await engine.dispose()


@pytest.mark.asyncio
async def test_sqlalchemy_repository_update_missing_raises_value_error(tmp_path: Path) -> None:
    db_file = tmp_path / "execution_record.db"
    engine = create_engine(f"sqlite+aiosqlite:///{db_file}")
    await init_db(engine)

    repository = SQLAlchemyExecutionRecordRepository(create_session_factory(engine))
    record = build_execution_record(id=str(uuid4()), order_id="order-1", worker_id="worker-1")

    with pytest.raises(ValueError, match=record.id):
        await repository.update(record)

    await engine.dispose()


def test_ensure_utc_keeps_aware_datetime() -> None:
    aware = datetime.now(UTC)

    assert _ensure_utc(aware) is aware
