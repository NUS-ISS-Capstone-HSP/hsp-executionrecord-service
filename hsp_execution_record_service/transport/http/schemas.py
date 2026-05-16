from pydantic import BaseModel, ConfigDict, Field


class StartServiceRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "order_id": "order-123",
                "worker_id": "worker-456",
            }
        },
    )

    order_id: str = Field(
        min_length=1,
        max_length=64,
        description="Order id to start service for.",
    )
    worker_id: str = Field(
        min_length=1,
        max_length=64,
        description="Worker id assigned to the order.",
    )


class ExecutionRecordResponse(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "id": "6f88f9f2-65fd-4ef7-80de-2c96d8ab7b5b",
                "order_id": "order-123",
                "worker_id": "worker-456",
                "status": "STARTED",
                "start_time": "2026-03-18T12:34:56+00:00",
                "end_time": None,
                "duration_minutes": None,
                "created_at": "2026-03-18T12:34:56+00:00",
                "updated_at": "2026-03-18T12:34:56+00:00",
            }
        },
    )

    id: str = Field(description="Execution record id (UUID).")
    order_id: str = Field(description="Order id.")
    worker_id: str = Field(description="Worker id.")
    status: str = Field(description="Execution status.")
    start_time: str = Field(description="Service start time in ISO-8601 format.")
    end_time: str | None = Field(description="Service end time in ISO-8601 format.")
    duration_minutes: int | None = Field(description="Service duration in whole minutes.")
    created_at: str = Field(description="Creation time in ISO-8601 format.")
    updated_at: str = Field(description="Last update time in ISO-8601 format.")


class QueryServiceRecordsResponse(BaseModel):
    records: list[ExecutionRecordResponse] = Field(description="Execution records.")
