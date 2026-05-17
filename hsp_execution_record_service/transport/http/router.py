from typing import Annotated

from fastapi import APIRouter, Header, Path, Query

from hsp_execution_record_service.service.execution_record_service import (
    ExecutionRecordService,
    parse_actor,
)
from hsp_execution_record_service.transport.http.mapper import to_http_response
from hsp_execution_record_service.transport.http.schemas import (
    ExecutionRecordResponse,
    QueryServiceRecordsResponse,
    StartServiceRequest,
)

ActorUserHeader = Annotated[str, Header(alias="X-User-Id", description="Caller user id.")]
ActorRoleHeader = Annotated[str, Header(alias="X-User-Role", description="Caller role.")]


def build_router(execution_record_service: ExecutionRecordService) -> APIRouter:
    router = APIRouter(prefix="/api/execution/v1", tags=["execution-records"])

    @router.post(
        "/services/start",
        response_model=ExecutionRecordResponse,
        status_code=201,
        summary="Start service",
        description="Create a STARTED execution record for an assigned worker order.",
        response_description="Started execution record.",
        responses={
            400: {"description": "Business validation failed."},
            403: {"description": "Caller is not allowed to start this service."},
            409: {"description": "Service was already started or completed."},
            422: {"description": "Request payload validation failed."},
        },
    )
    async def start_service(
        payload: StartServiceRequest,
        actor_user_id: ActorUserHeader,
        actor_role: ActorRoleHeader,
    ) -> ExecutionRecordResponse:
        actor = parse_actor(actor_user_id, actor_role)
        record = await execution_record_service.start_service(
            payload.order_id,
            payload.worker_id,
            actor,
        )
        return to_http_response(record)

    @router.post(
        "/services/{record_id}/end",
        response_model=ExecutionRecordResponse,
        summary="End service",
        description="Complete a STARTED execution record and calculate duration.",
        response_description="Completed execution record.",
        responses={
            400: {"description": "Business validation failed."},
            403: {"description": "Caller is not allowed to end this service."},
            404: {"description": "Execution record was not found."},
            409: {"description": "Execution record is not STARTED."},
        },
    )
    async def end_service(
        actor_user_id: ActorUserHeader,
        actor_role: ActorRoleHeader,
        record_id: str = Path(..., description="Execution record id (UUID)."),
    ) -> ExecutionRecordResponse:
        actor = parse_actor(actor_user_id, actor_role)
        record = await execution_record_service.end_service(record_id, actor)
        return to_http_response(record)

    @router.get(
        "/services/records",
        response_model=QueryServiceRecordsResponse,
        summary="Query service records",
        description="Workers can query own records. Admin, staff and owner can query all records.",
        response_description="Execution record list.",
        responses={
            400: {"description": "Business validation failed."},
            403: {"description": "Caller is not allowed to query these records."},
        },
    )
    async def query_service_records(
        actor_user_id: ActorUserHeader,
        actor_role: ActorRoleHeader,
        worker_id: str | None = Query(None, description="Optional worker id filter."),
    ) -> QueryServiceRecordsResponse:
        actor = parse_actor(actor_user_id, actor_role)
        records = await execution_record_service.query_service_records(actor, worker_id)
        return QueryServiceRecordsResponse(records=[to_http_response(record) for record in records])

    return router
