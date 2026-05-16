import grpc
import pytest
import pytest_asyncio

from hsp_execution_record_service.repository.in_memory import InMemoryExecutionRecordRepository
from hsp_execution_record_service.service.execution_record_service import ExecutionRecordService
from hsp_execution_record_service.transport.grpc.service import ExecutionRecordGrpcService
from rpc.echo.v1 import echo_pb2, echo_pb2_grpc


@pytest_asyncio.fixture
async def grpc_stub() -> echo_pb2_grpc.ExecutionRecordServiceStub:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())

    server = grpc.aio.server()
    echo_pb2_grpc.add_ExecutionRecordServiceServicer_to_server(
        ExecutionRecordGrpcService(service),
        server,
    )
    port = server.add_insecure_port("127.0.0.1:0")
    await server.start()

    channel = grpc.aio.insecure_channel(f"127.0.0.1:{port}")
    stub = echo_pb2_grpc.ExecutionRecordServiceStub(channel)

    try:
        yield stub
    finally:
        await channel.close()
        await server.stop(0)


@pytest.mark.asyncio
async def test_health_success(grpc_stub: echo_pb2_grpc.ExecutionRecordServiceStub) -> None:
    response = await grpc_stub.Health(echo_pb2.HealthRequest())

    assert response.status == "ok"


@pytest.mark.asyncio
async def test_start_end_and_query_service_success(
    grpc_stub: echo_pb2_grpc.ExecutionRecordServiceStub,
) -> None:
    created = await grpc_stub.StartService(
        echo_pb2.StartServiceRequest(
            order_id="order-1",
            worker_id="worker-1",
            actor_user_id="worker-1",
            actor_role="worker",
        ),
    )
    completed = await grpc_stub.EndService(
        echo_pb2.EndServiceRequest(
            record_id=created.record.id,
            actor_user_id="worker-1",
            actor_role="worker",
        ),
    )
    queried = await grpc_stub.QueryServiceRecords(
        echo_pb2.QueryServiceRecordsRequest(actor_user_id="worker-1", actor_role="worker"),
    )

    assert created.record.order_id == "order-1"
    assert created.record.status == "STARTED"
    assert completed.record.status == "COMPLETED"
    assert len(queried.records) == 1


@pytest.mark.asyncio
async def test_start_service_invalid_argument(
    grpc_stub: echo_pb2_grpc.ExecutionRecordServiceStub,
) -> None:
    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.StartService(
            echo_pb2.StartServiceRequest(
                order_id="",
                worker_id="worker-1",
                actor_user_id="worker-1",
                actor_role="worker",
            ),
        )

    assert exc_info.value.code() == grpc.StatusCode.INVALID_ARGUMENT


@pytest.mark.asyncio
async def test_end_service_not_found(grpc_stub: echo_pb2_grpc.ExecutionRecordServiceStub) -> None:
    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.EndService(
            echo_pb2.EndServiceRequest(
                record_id="missing",
                actor_user_id="worker-1",
                actor_role="worker",
            ),
        )

    assert exc_info.value.code() == grpc.StatusCode.NOT_FOUND


@pytest.mark.asyncio
async def test_query_service_records_permission_denied(
    grpc_stub: echo_pb2_grpc.ExecutionRecordServiceStub,
) -> None:
    with pytest.raises(grpc.aio.AioRpcError) as exc_info:
        await grpc_stub.QueryServiceRecords(
            echo_pb2.QueryServiceRecordsRequest(
                actor_user_id="worker-1",
                actor_role="worker",
                worker_id="worker-2",
            ),
        )

    assert exc_info.value.code() == grpc.StatusCode.PERMISSION_DENIED
