import grpc

from hsp_execution_record_service.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from hsp_execution_record_service.service.execution_record_service import (
    ExecutionRecordService,
    parse_actor,
)
from hsp_execution_record_service.transport.grpc.mapper import to_grpc_record
from rpc.echo.v1 import echo_pb2, echo_pb2_grpc


class ExecutionRecordGrpcService(echo_pb2_grpc.ExecutionRecordServiceServicer):
    def __init__(self, execution_record_service: ExecutionRecordService) -> None:
        self._execution_record_service = execution_record_service

    async def StartService(
        self,
        request: echo_pb2.StartServiceRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.StartServiceResponse:
        try:
            actor = parse_actor(request.actor_user_id, request.actor_role)
            record = await self._execution_record_service.start_service(
                request.order_id,
                request.worker_id,
                actor,
            )
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except ForbiddenError as exc:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))
        except ConflictError as exc:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return echo_pb2.StartServiceResponse(record=to_grpc_record(record))

    async def EndService(
        self,
        request: echo_pb2.EndServiceRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.EndServiceResponse:
        try:
            actor = parse_actor(request.actor_user_id, request.actor_role)
            record = await self._execution_record_service.end_service(request.record_id, actor)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except ForbiddenError as exc:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))
        except NotFoundError as exc:
            await context.abort(grpc.StatusCode.NOT_FOUND, str(exc))
        except ConflictError as exc:
            await context.abort(grpc.StatusCode.FAILED_PRECONDITION, str(exc))
        return echo_pb2.EndServiceResponse(record=to_grpc_record(record))

    async def QueryServiceRecords(
        self,
        request: echo_pb2.QueryServiceRecordsRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.QueryServiceRecordsResponse:
        try:
            actor = parse_actor(request.actor_user_id, request.actor_role)
            worker_id = request.worker_id or None
            records = await self._execution_record_service.query_service_records(actor, worker_id)
        except ValidationError as exc:
            await context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
        except ForbiddenError as exc:
            await context.abort(grpc.StatusCode.PERMISSION_DENIED, str(exc))
        return echo_pb2.QueryServiceRecordsResponse(
            records=[to_grpc_record(record) for record in records],
        )

    async def Health(
        self,
        request: echo_pb2.HealthRequest,
        context: grpc.aio.ServicerContext,
    ) -> echo_pb2.HealthResponse:
        del request, context
        return echo_pb2.HealthResponse(status="ok")
