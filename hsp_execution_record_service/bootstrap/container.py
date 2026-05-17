from dataclasses import dataclass

import grpc
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from hsp_execution_record_service.config import Settings, get_settings
from hsp_execution_record_service.infrastructure.db import (
    create_engine,
    create_session_factory,
    init_db,
)
from hsp_execution_record_service.repository.in_memory import InMemoryExecutionRecordRepository
from hsp_execution_record_service.repository.interfaces import ExecutionRecordRepository
from hsp_execution_record_service.repository.mysql import SQLAlchemyExecutionRecordRepository
from hsp_execution_record_service.service.execution_record_service import ExecutionRecordService
from hsp_execution_record_service.transport.grpc.server import build_grpc_server
from hsp_execution_record_service.transport.http.app import create_http_app


@dataclass(slots=True)
class AppContainer:
    settings: Settings
    engine: AsyncEngine | None
    session_factory: async_sessionmaker[AsyncSession] | None
    execution_record_repository: ExecutionRecordRepository
    execution_record_service: ExecutionRecordService
    http_app: FastAPI
    grpc_server: grpc.aio.Server


async def build_container() -> AppContainer:
    settings = get_settings()
    repository: ExecutionRecordRepository

    if settings.use_mock_repository:
        engine = None
        session_factory = None
        repository = InMemoryExecutionRecordRepository()
    else:
        engine = create_engine(settings.mysql_dsn)
        await init_db(engine)
        session_factory = create_session_factory(engine)
        repository = SQLAlchemyExecutionRecordRepository(session_factory)

    execution_record_service = ExecutionRecordService(repository)
    http_app = create_http_app(execution_record_service)
    grpc_server = build_grpc_server(settings, execution_record_service)

    return AppContainer(
        settings=settings,
        engine=engine,
        session_factory=session_factory,
        execution_record_repository=repository,
        execution_record_service=execution_record_service,
        http_app=http_app,
        grpc_server=grpc_server,
    )
