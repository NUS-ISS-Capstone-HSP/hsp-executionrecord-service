from pathlib import Path

import pytest

from hsp_execution_record_service.bootstrap.container import build_container
from hsp_execution_record_service.config import get_settings
from hsp_execution_record_service.repository.in_memory import InMemoryExecutionRecordRepository
from hsp_execution_record_service.repository.mysql import SQLAlchemyExecutionRecordRepository
from hsp_execution_record_service.service.execution_record_service import parse_actor


@pytest.mark.asyncio
async def test_build_container_with_mock_repository(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HSP_EXECUTION_RECORD_SERVICE_USE_MOCK_REPOSITORY", "true")
    monkeypatch.setenv("HSP_EXECUTION_RECORD_SERVICE_MYSQL_DSN", "mysql+aiomysql://not-used")
    monkeypatch.setenv("HSP_EXECUTION_RECORD_SERVICE_GRPC_PORT", "0")
    get_settings.cache_clear()

    container = await build_container()

    assert isinstance(container.execution_record_repository, InMemoryExecutionRecordRepository)
    assert container.engine is None
    assert container.session_factory is None

    get_settings.cache_clear()


@pytest.mark.asyncio
async def test_build_container_with_sqlalchemy_repository(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    db_file = tmp_path / "container.db"
    monkeypatch.setenv("HSP_EXECUTION_RECORD_SERVICE_USE_MOCK_REPOSITORY", "false")
    monkeypatch.setenv("HSP_EXECUTION_RECORD_SERVICE_MYSQL_DSN", f"sqlite+aiosqlite:///{db_file}")
    monkeypatch.setenv("HSP_EXECUTION_RECORD_SERVICE_GRPC_PORT", "0")
    get_settings.cache_clear()

    container = await build_container()

    assert isinstance(container.execution_record_repository, SQLAlchemyExecutionRecordRepository)
    assert container.engine is not None
    assert container.session_factory is not None

    created = await container.execution_record_service.start_service(
        "order-1",
        "worker-1",
        parse_actor("worker-1", "worker"),
    )
    records = await container.execution_record_service.query_service_records(
        parse_actor("admin-1", "admin"),
    )
    assert [record.id for record in records] == [created.id]

    if container.engine is not None:
        await container.engine.dispose()
    get_settings.cache_clear()
