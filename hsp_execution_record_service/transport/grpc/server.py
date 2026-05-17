import grpc

from hsp_execution_record_service.config import Settings
from hsp_execution_record_service.service.execution_record_service import ExecutionRecordService
from hsp_execution_record_service.transport.grpc.service import ExecutionRecordGrpcService
from rpc.echo.v1 import echo_pb2_grpc


def build_grpc_server(
    settings: Settings,
    execution_record_service: ExecutionRecordService,
) -> grpc.aio.Server:
    server = grpc.aio.server()
    echo_pb2_grpc.add_ExecutionRecordServiceServicer_to_server(
        ExecutionRecordGrpcService(execution_record_service),
        server,
    )
    server.add_insecure_port(f"{settings.grpc_host}:{settings.grpc_port}")
    return server
