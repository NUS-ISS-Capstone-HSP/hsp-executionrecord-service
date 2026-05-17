from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum


class RecordStatus(StrEnum):
    STARTED = "STARTED"
    COMPLETED = "COMPLETED"


class UserRole(StrEnum):
    WORKER = "worker"
    ADMIN = "admin"
    STAFF = "staff"
    OWNER = "owner"


@dataclass(frozen=True, slots=True)
class Actor:
    user_id: str
    role: UserRole


@dataclass(slots=True)
class ExecutionRecord:
    id: str
    order_id: str
    worker_id: str
    status: RecordStatus
    start_time: datetime
    end_time: datetime | None
    duration_minutes: int | None
    created_at: datetime
    updated_at: datetime
