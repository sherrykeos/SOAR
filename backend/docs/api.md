# SOAR Backend REST API

SOAR provides a clean, local-first REST API built with FastAPI to interact with the agent, file storage, progress event checkpoints, and configured models.

---

## 1. Running the API

The API reads its host and port settings directly from `config/config.yaml`:

```yaml
api:
  host: "127.0.0.1"
  port: 8000
  reload: true
```

### Start Command:
```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

---

## 2. API Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| **GET** | `/api/health` | Health and operational status check |
| **POST** | `/api/tasks` | Execute user task with adaptive model routing |
| **GET** | `/api/tasks/{run_id}/events` | Retrieve execution progress checkpoints for a task run |
| **POST** | `/api/files/upload` | Upload and store local file in managed storage |
| **GET** | `/api/files` | List managed files with pagination |
| **GET** | `/api/files/{file_id}` | Retrieve metadata for a managed file |
| **GET** | `/api/files/{file_id}/download` | Download binary content of a managed file |
| **DELETE** | `/api/files/{file_id}` | Delete a managed file and its metadata |
| **GET** | `/api/models` | List configured local models and availability status |

---

## 3. Detailed Endpoint Documentation

### `GET /api/health`
Checks whether the SOAR backend is alive.

#### Response:
```json
{
  "status": "ok",
  "app": "SOAR",
  "version": "0.1.0"
}
```

---

### `POST /api/tasks`
Submits a user prompt to the orchestrator. Automatically classifies the task and routes it to the optimal local model.

#### Request:
```json
{
  "task": "Explain why boiler vibration requires immediate maintenance.",
  "model": null
}
```

#### Response:
```json
{
  "run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "status": "completed",
  "answer": "Abnormal vibration in industrial boilers often signals mechanical resonance, bearing wear, or cavitation...",
  "model": "qwen2:4b",
  "execution_mode": "direct_answer",
  "citations": [],
  "events": [
    {
      "event_id": "...",
      "stage": "CLASSIFYING",
      "status": "STARTED",
      "message": "Classifying task",
      "timestamp": "2026-09-09T14:40:00Z"
    }
  ]
}
```

---

### `GET /api/tasks/{run_id}/events`
Retrieves the complete sequence of execution checkpoints associated with `run_id`.

#### Response:
```json
{
  "run_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "events": [
    {
      "event_id": "e-1",
      "stage": "CLASSIFYING",
      "status": "STARTED",
      "message": "Classifying task",
      "timestamp": "2026-09-09T14:40:00Z",
      "metadata": {}
    },
    {
      "event_id": "e-2",
      "stage": "MODEL_SELECTING",
      "status": "COMPLETED",
      "message": "Model selected — qwen2:4b",
      "timestamp": "2026-09-09T14:40:01Z",
      "metadata": {}
    },
    {
      "event_id": "e-3",
      "stage": "COMPLETED",
      "status": "COMPLETED",
      "message": "Task completed",
      "timestamp": "2026-09-09T14:40:03Z",
      "metadata": {
        "execution_mode": "direct_answer",
        "model": "qwen2:4b"
      }
    }
  ]
}
```

---

### `POST /api/files/upload`
Uploads a file into managed storage (`data/files/`). Protected against path traversal attacks.

- **Content-Type**: `multipart/form-data`
- **Body**: `file: (binary)`

#### Response:
```json
{
  "file_id": "d7c72f20-d0bc-4ed0-a88d-f3d1707c9aec",
  "original_filename": "boiler_spec.pdf",
  "size_bytes": 1048576,
  "mime_type": "application/pdf",
  "sha256": "9c9989831871c414f6ad2ff85cfc5aa76caa71184daaeb89f45fa70de4a5950a",
  "created_at": "2026-09-09T14:40:00Z"
}
```

---

### `GET /api/files`
Lists all managed files.

- **Query Parameters**:
  - `limit`: int (default: 50)
  - `offset`: int (default: 0)

#### Response:
```json
{
  "total": 1,
  "files": [
    {
      "file_id": "d7c72f20-d0bc-4ed0-a88d-f3d1707c9aec",
      "original_filename": "boiler_spec.pdf",
      "size_bytes": 1048576,
      "mime_type": "application/pdf",
      "sha256": "9c99...",
      "created_at": "2026-09-09T14:40:00Z"
    }
  ]
}
```

---

### `GET /api/files/{file_id}/download`
Downloads the binary contents of the stored file.

- **Response**: Binary stream with `Content-Disposition: attachment; filename="boiler_spec.pdf"`.

---

### `DELETE /api/files/{file_id}`
Deletes the file and metadata from managed storage.

#### Response:
```json
{
  "status": "deleted",
  "file_id": "d7c72f20-d0bc-4ed0-a88d-f3d1707c9aec"
}
```

---

### `GET /api/models`
Returns the list of configured models from `config/config.yaml` along with their local availability status.

#### Response:
```json
{
  "default_model": "qwen3:1.7b",
  "models": [
    {
      "id": "qwen3:1.7b",
      "provider": "ollama",
      "capabilities": ["general", "reasoning"],
      "priority": 10,
      "enabled": true,
      "available": true,
      "timeout": 180.0
    },
    {
      "id": "qwen2:4b",
      "provider": "ollama",
      "capabilities": ["reasoning"],
      "priority": 20,
      "enabled": true,
      "available": true,
      "timeout": 15.0
    },
    {
      "id": "qwen2.5-coder:1.5b",
      "provider": "ollama",
      "capabilities": ["coding"],
      "priority": 15,
      "enabled": true,
      "available": true,
      "timeout": 180.0
    },
    {
      "id": "qwen2.5vl:3b",
      "provider": "ollama",
      "capabilities": ["vision"],
      "priority": 15,
      "enabled": true,
      "available": true,
      "timeout": 180.0
    }
  ]
}
```

---

## 4. Execution Architecture: Synchronous vs. Asynchronous

For the current MVP milestone, task execution through `POST /api/tasks` runs synchronously to maintain strict determinism, zero complexity overhead, and immediate responses for single-turn and multi-step tasks.

Because every execution generates and correlates a persistent `run_id`, the architecture is already fully prepared for future background task execution and SSE/WebSocket streaming without altering core interfaces.
