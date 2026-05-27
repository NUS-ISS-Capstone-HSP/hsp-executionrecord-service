from fastapi.testclient import TestClient

from hsp_execution_record_service.repository.in_memory import InMemoryExecutionRecordRepository
from hsp_execution_record_service.service.execution_record_service import ExecutionRecordService
from hsp_execution_record_service.transport.http.app import create_http_app

WORKER_HEADERS = {"X-User-Id": "worker-1", "X-User-Role": "worker"}
ADMIN_HEADERS = {"X-User-Id": "admin-1", "X-User-Role": "admin"}


def build_client() -> TestClient:
    service = ExecutionRecordService(InMemoryExecutionRecordRepository())
    app = create_http_app(service)
    return TestClient(app)


def test_healthz_success() -> None:
    client = build_client()

    response = client.get("/healthz")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_start_and_end_service_success() -> None:
    client = build_client()

    response = client.post(
        "/api/execution/v1/services/start",
        json={"order_id": "order-1", "worker_id": "worker-1"},
        headers=WORKER_HEADERS,
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["order_id"] == "order-1"
    assert payload["worker_id"] == "worker-1"
    assert payload["status"] == "STARTED"

    end_response = client.post(
        f"/api/execution/v1/services/{payload['id']}/end",
        headers=WORKER_HEADERS,
    )

    assert end_response.status_code == 200
    assert end_response.json()["status"] == "COMPLETED"


def test_start_service_validation_error() -> None:
    client = build_client()

    response = client.post(
        "/api/execution/v1/services/start",
        json={"order_id": "", "worker_id": "worker-1"},
        headers=WORKER_HEADERS,
    )

    assert response.status_code == 422


def test_start_service_forbidden_for_other_worker() -> None:
    client = build_client()

    response = client.post(
        "/api/execution/v1/services/start",
        json={"order_id": "order-1", "worker_id": "worker-2"},
        headers=WORKER_HEADERS,
    )

    assert response.status_code == 403


def test_start_service_conflict_for_duplicate_order() -> None:
    client = build_client()
    payload = {"order_id": "order-1", "worker_id": "worker-1"}
    client.post("/api/execution/v1/services/start", json=payload, headers=WORKER_HEADERS)

    response = client.post("/api/execution/v1/services/start", json=payload, headers=WORKER_HEADERS)

    assert response.status_code == 409


def test_query_service_records_domain_validation_error() -> None:
    client = build_client()

    response = client.get(
        "/api/execution/v1/services/records?worker_id=%20",
        headers=ADMIN_HEADERS,
    )

    assert response.status_code == 400


def test_end_service_not_found() -> None:
    client = build_client()

    response = client.post(
        "/api/execution/v1/services/missing-id/end",
        headers=WORKER_HEADERS,
    )

    assert response.status_code == 404


def test_query_service_records_worker_and_admin_scope() -> None:
    client = build_client()
    client.post(
        "/api/execution/v1/services/start",
        json={"order_id": "order-1", "worker_id": "worker-1"},
        headers=WORKER_HEADERS,
    )
    client.post(
        "/api/execution/v1/services/start",
        json={"order_id": "order-2", "worker_id": "worker-2"},
        headers={"X-User-Id": "worker-2", "X-User-Role": "worker"},
    )

    worker_response = client.get("/api/execution/v1/services/records", headers=WORKER_HEADERS)
    admin_response = client.get("/api/execution/v1/services/records", headers=ADMIN_HEADERS)
    forbidden_response = client.get(
        "/api/execution/v1/services/records?worker_id=worker-2",
        headers=WORKER_HEADERS,
    )

    assert worker_response.status_code == 200
    assert len(worker_response.json()["records"]) == 1
    assert admin_response.status_code == 200
    assert len(admin_response.json()["records"]) == 2
    assert forbidden_response.status_code == 403
