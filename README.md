# HSP Execution Record Service

Python 后端服务，记录工人服务执行过程，提供 HTTP + gRPC 双入口。当前 MVP 支持
Start Service、End Service、Query Service Records；Photo Upload 暂不实现，仅保留后续 TODO。

## 架构

- `domain`：领域模型与错误定义
- `repository`：仓储接口与实现（MySQL / InMemory）
- `service`：核心业务逻辑（与 transport 无关）
- `transport/http`：FastAPI controller、schema、mapper
- `transport/grpc`：gRPC servicer、mapper
- `bootstrap`：依赖装配（单进程启动 HTTP + gRPC）

## 功能接口

HTTP:
- `GET /healthz`
- `POST /api/execution/v1/services/start`
- `POST /api/execution/v1/services/{record_id}/end`
- `GET /api/execution/v1/services/records`

gRPC:
- `StartService`
- `EndService`
- `QueryServiceRecords`
- `Health`

## MVP 规则

- worker 只能 start 自己的 order；当前 order assignment 使用 fake implementation，后续联调
  order-service 或 dispatch-service。
- 已经 STARTED 或 COMPLETED 的 order 不能重复 start。
- 只有 STARTED 的 execution record 可以 end；end 时自动写入 `end_time` 并计算
  `duration_minutes`。
- worker 只能查询自己的 records；admin、staff、owner 可以查询全部，也可以用
  `worker_id` 过滤。
- Photo Upload 暂不实现。

## 本地开发

0. 准备 Python 环境（建议 3.12）

```bash
python --version
```

1. 准备环境变量文件

```bash
cp .env.example .env
```

如果服务在本机运行（`make run`），MySQL 也在本机 Docker 映射端口（如 `127.0.0.1:3306`），请将 `.env` 中的 `HSP_EXECUTION_RECORD_SERVICE_MYSQL_DSN` 改为：

```env
HSP_EXECUTION_RECORD_SERVICE_MYSQL_DSN=mysql+aiomysql://<username>:<pwd>@127.0.0.1:3306/execution_db
```

2. 安装依赖

```bash
make install
```

3. 生成 gRPC 代码（修改 proto 后执行）

```bash
make proto-gen
```

4. 运行服务（HTTP 8080 + gRPC 50051）

```bash
make run
```

5. 验证服务

```bash
curl http://127.0.0.1:8080/healthz
```

返回 `{"status":"ok"}` 表示 HTTP 服务启动成功。

6. 测试 HTTP 接口

Start Service:

```bash
curl -X POST http://127.0.0.1:8080/api/execution/v1/services/start \
  -H 'Content-Type: application/json' \
  -H 'X-User-Id: worker-1' \
  -H 'X-User-Role: worker' \
  -d '{"order_id":"order-1","worker_id":"worker-1"}'
```

End Service:

```bash
curl -X POST http://127.0.0.1:8080/api/execution/v1/services/<record_id>/end \
  -H 'X-User-Id: worker-1' \
  -H 'X-User-Role: worker'
```

Query Service Records:

```bash
curl http://127.0.0.1:8080/api/execution/v1/services/records \
  -H 'X-User-Id: admin-1' \
  -H 'X-User-Role: admin'
```

7. 查看 Swagger/OpenAPI 文档

- Swagger UI: `http://127.0.0.1:8080/docs`
- OpenAPI JSON: `http://127.0.0.1:8080/openapi.json`

## 质量检查

```bash
make lint
make test-unit
make coverage
make swagger
```

## Docker

```bash
make docker-build
```

## 环境变量

参考 `.env.example`，关键项：
- `HSP_EXECUTION_RECORD_SERVICE_HTTP_HOST` / `HSP_EXECUTION_RECORD_SERVICE_HTTP_PORT`
- `HSP_EXECUTION_RECORD_SERVICE_GRPC_HOST` / `HSP_EXECUTION_RECORD_SERVICE_GRPC_PORT`
- `HSP_EXECUTION_RECORD_SERVICE_MYSQL_DSN`
- `HSP_EXECUTION_RECORD_SERVICE_USE_MOCK_REPOSITORY`
