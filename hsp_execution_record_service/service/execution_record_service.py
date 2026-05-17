from datetime import UTC, datetime
from typing import Protocol
from uuid import uuid4

from hsp_execution_record_service.domain.errors import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ValidationError,
)
from hsp_execution_record_service.domain.models import (
    Actor,
    ExecutionRecord,
    RecordStatus,
    UserRole,
)
from hsp_execution_record_service.repository.interfaces import ExecutionRecordRepository


class OrderAssignmentClient(Protocol):
    async def is_order_assigned_to_worker(self, order_id: str, worker_id: str) -> bool:
        ...


class FakeOrderAssignmentClient(OrderAssignmentClient):
    async def is_order_assigned_to_worker(self, order_id: str, worker_id: str) -> bool:
        del order_id, worker_id
        # TODO: Replace this fake with order-service or dispatch-service lookup.
        return True


# TODO: Add photo upload workflow after the MVP service record flow is integrated.


class ExecutionRecordService:
    def __init__(
        self,
        repository: ExecutionRecordRepository,
        order_assignment_client: OrderAssignmentClient | None = None,
    ) -> None:
        self._repository = repository
        self._order_assignment_client = order_assignment_client or FakeOrderAssignmentClient()

    async def start_service(self, order_id: str, worker_id: str, actor: Actor) -> ExecutionRecord:
        normalized_order_id = _normalize_required(order_id, "order_id")
        normalized_worker_id = _normalize_required(worker_id, "worker_id")
        self._ensure_worker_owns_action(actor, normalized_worker_id)

        is_assigned = await self._order_assignment_client.is_order_assigned_to_worker(
            normalized_order_id,
            normalized_worker_id,
        )
        if not is_assigned:
            raise ForbiddenError("worker can only start an assigned order")

        existing = await self._repository.get_by_order_id(normalized_order_id)
        if existing is not None:
            if existing.status == RecordStatus.STARTED:
                raise ConflictError("service has already been started")
            raise ConflictError("service has already been completed")

        now = datetime.now(UTC)
        record = ExecutionRecord(
            id=str(uuid4()),
            order_id=normalized_order_id,
            worker_id=normalized_worker_id,
            status=RecordStatus.STARTED,
            start_time=now,
            end_time=None,
            duration_minutes=None,
            created_at=now,
            updated_at=now,
        )
        return await self._repository.create(record)

    async def end_service(self, record_id: str, actor: Actor) -> ExecutionRecord:
        normalized_record_id = _normalize_required(record_id, "record_id")
        record = await self._repository.get_by_id(normalized_record_id)
        if record is None:
            raise NotFoundError(f"execution record '{normalized_record_id}' not found")

        self._ensure_worker_owns_action(actor, record.worker_id)
        if record.status != RecordStatus.STARTED:
            raise ConflictError("only STARTED records can be ended")

        now = datetime.now(UTC)
        elapsed_seconds = max(0, int((now - record.start_time).total_seconds()))
        record.status = RecordStatus.COMPLETED
        record.end_time = now
        record.duration_minutes = elapsed_seconds // 60
        record.updated_at = now
        return await self._repository.update(record)

    async def query_service_records(
        self,
        actor: Actor,
        worker_id: str | None = None,
    ) -> list[ExecutionRecord]:
        normalized_worker_id = worker_id.strip() if worker_id is not None else None
        if normalized_worker_id == "":
            raise ValidationError("worker_id must not be empty")

        if actor.role == UserRole.WORKER:
            if normalized_worker_id is not None and normalized_worker_id != actor.user_id:
                raise ForbiddenError("worker can only query own records")
            return await self._repository.list_by_worker(actor.user_id)

        if actor.role in {UserRole.ADMIN, UserRole.STAFF, UserRole.OWNER}:
            if normalized_worker_id is not None:
                return await self._repository.list_by_worker(normalized_worker_id)
            return await self._repository.list_all()

        raise ForbiddenError("role is not allowed to query service records")

    def _ensure_worker_owns_action(self, actor: Actor, worker_id: str) -> None:
        if actor.role == UserRole.WORKER and actor.user_id != worker_id:
            raise ForbiddenError("worker can only operate own service record")


def parse_actor(user_id: str, role: str) -> Actor:
    normalized_user_id = _normalize_required(user_id, "actor_user_id")
    normalized_role = _normalize_required(role, "actor_role").lower()
    try:
        parsed_role = UserRole(normalized_role)
    except ValueError as exc:
        allowed_roles = ", ".join(role.value for role in UserRole)
        raise ValidationError(f"actor_role must be one of: {allowed_roles}") from exc
    return Actor(user_id=normalized_user_id, role=parsed_role)


def _normalize_required(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValidationError(f"{field_name} must not be empty")
    return normalized
