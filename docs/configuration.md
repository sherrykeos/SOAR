# SOAR Centralized Application Configuration

SOAR (Sovereign On-premise Agentic Reasoning) uses a centralized, typed, and dynamic configuration system.

A single configuration file controls the entire application:

```text
SOAR/
├── config/
│   └── config.yaml
├── app/
│   └── ...
```

A user can move SOAR to another machine, edit `config/config.yaml`, and run the system without modifying Python source code.

---

## 1. Architecture

```text
                  config/config.yaml
                          ↓
                app/config/loader.py
           (YAML parsing + Validation + Path resolution)
                          ↓
                app/config/schema.py
             (Typed SOARConfig Dataclasses)
                          ↓
       ┌──────────────────┼──────────────────┐
       ↓                  ↓                  ↓
  ModelManager     LocalFileStorage   DatabaseManager
(Dynamic Models)    (Storage Root)     (SQLite Path)
       ↓                  ↓                  ↓
  ModelRouter        VectorStore        PythonSandbox
(Capability-Based)   (ChromaDB)          (Workspace)
       ↓
     Agent
```

---

## 2. Configuration Sections

### `app`
Basic application metadata and debugging flags.
```yaml
app:
  name: "SOAR"
  environment: "development"
  debug: false
```

---

### `models` (Dynamic Model Pool)
SOAR's model registry is populated directly from configuration. Any model supported by an existing provider (e.g. `ollama`, `mock`) can be added or replaced through `config.yaml` without changing Python source code.

```yaml
models:
  - id: "qwen3:1.7b"
    provider: "ollama"
    capabilities:
      - "general"
      - "reasoning"
    priority: 10
    enabled: true
    timeout: 180

  - id: "qwen2:4b"
    provider: "ollama"
    capabilities:
      - "reasoning"
    priority: 20
    enabled: true
    timeout: 15

  - id: "qwen2.5-coder:1.5b"
    provider: "ollama"
    capabilities:
      - "coding"
    priority: 15
    enabled: true
    timeout: 180

  - id: "qwen2.5vl:3b"
    provider: "ollama"
    capabilities:
      - "vision"
    priority: 15
    enabled: true
    timeout: 180
```

#### How to Add a New Model
To add a new local model (e.g., `deepseek-coder:6.7b` for coding):
1. Pull the model locally: `ollama pull deepseek-coder:6.7b`
2. Add the entry to `config/config.yaml`:
   ```yaml
   - id: "deepseek-coder:6.7b"
     provider: "ollama"
     capabilities:
       - "coding"
     priority: 5
     enabled: true
   ```
3. Restart SOAR. The `ModelRouter` will dynamically prioritize and select `deepseek-coder:6.7b` for coding tasks.

*Note: Adding a model supported by an existing provider (such as Ollama) requires configuration only. Adding an entirely new inference provider backend requires implementing a corresponding `ModelAdapter`.*

---

### `ollama`
Local Ollama inference endpoint.
```yaml
ollama:
  base_url: "http://localhost:11434"
  timeout: 180.0
```

---

### `storage` & `database`
Paths for managed file storage and SQLite metadata.
```yaml
storage:
  root: "./data/files"
  max_file_size_bytes: 52428800  # 50 MB
  allow_empty: true

database:
  path: "./data/soar.db"
```

---

### `vector_store` & `embeddings`
Local ChromaDB and BGE-M3 embedding settings.
```yaml
vector_store:
  backend: "chroma"
  path: "./data/chroma"
  collection_name: "soar_knowledge"

embeddings:
  model_name_or_path: "BAAI/bge-m3"
  dimension: 1024
  device: null  # null = auto-detect (CUDA if available, else CPU)
  normalize_embeddings: true
  batch_size: 32
```

---

### `agent` & `sandbox`
Agent iteration limits, default fallback model, and Python sandbox isolation directory.
```yaml
agent:
  max_iterations: 5
  default_model_id: "qwen3:1.7b"
  hard_model_timeout: 15.0

sandbox:
  root: "./sandbox"
  timeout: 10
```

---

### `security`
Application-level air-gap policy.
```yaml
security:
  allow_external_network: false
```
*Note: `allow_external_network` is an internal application policy flag and does not replace OS-level firewall or network isolation.*

---

## 3. Hardware Portability & Deployment

All relative paths (e.g. `./data/files`, `./data/soar.db`, `./data/chroma`) resolve automatically relative to the SOAR project root directory.

To move SOAR to another machine:
1. Copy the SOAR project directory to the new machine.
2. Edit `config/config.yaml` to specify the local model pool and desired storage paths for the machine.
3. Start SOAR. No source code edits are necessary.

Changes to `config.yaml` take effect when the SOAR application starts or is restarted.
