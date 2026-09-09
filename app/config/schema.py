from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AppConfig:
    name: str = "SOAR"
    environment: str = "development"
    debug: bool = False


@dataclass
class ModelDefinitionConfig:
    id: str
    provider: str = "ollama"
    capabilities: List[str] = field(default_factory=lambda: ["general"])
    priority: int = 100
    enabled: bool = True
    timeout: Optional[float] = None
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OllamaConfig:
    base_url: str = "http://localhost:11434"
    timeout: float = 180.0


@dataclass
class StorageConfig:
    root: str = "./data/files"
    max_file_size_bytes: int = 52428800  # 50 MB
    allow_empty: bool = True


@dataclass
class DatabaseConfig:
    path: str = "./data/soar.db"


@dataclass
class VectorStoreConfig:
    backend: str = "chroma"
    path: str = "./data/chroma"
    collection_name: str = "soar_knowledge"


@dataclass
class EmbeddingsConfig:
    model_name_or_path: str = "BAAI/bge-m3"
    dimension: int = 1024
    device: Optional[str] = None
    normalize_embeddings: bool = True
    batch_size: int = 32


@dataclass
class VisionConfig:
    model: str = "qwen2.5vl:3b"
    base_url: str = "http://localhost:11434"
    backend: str = "ollama"
    timeout: int = 180
    temperature: float = 0.2


@dataclass
class RAGConfig:
    top_k: int = 5
    chunk_size: int = 500
    chunk_overlap: int = 50


@dataclass
class AgentConfig:
    max_iterations: int = 5
    default_model_id: str = "qwen3:1.7b"
    hard_model_timeout: float = 15.0


@dataclass
class SandboxConfig:
    root: str = "./sandbox"
    timeout: int = 10


@dataclass
class EventsConfig:
    enabled: bool = True


@dataclass
class SecurityConfig:
    allow_external_network: bool = False


@dataclass
class APIConfig:
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


@dataclass
class SOARConfig:
    """
    Root Typed Configuration for SOAR Sovereign AI Agent.
    Aggregates all subsystem configurations into a single, cohesive schema.
    """
    app: AppConfig = field(default_factory=AppConfig)
    models: List[ModelDefinitionConfig] = field(default_factory=list)
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    embeddings: EmbeddingsConfig = field(default_factory=EmbeddingsConfig)
    vision: VisionConfig = field(default_factory=VisionConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    sandbox: SandboxConfig = field(default_factory=SandboxConfig)
    events: EventsConfig = field(default_factory=EventsConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    api: APIConfig = field(default_factory=APIConfig)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SOARConfig":
        """Reconstructs a typed SOARConfig instance from a nested dictionary."""
        data = data or {}

        # Parse app
        app_cfg = AppConfig(**data.get("app", {})) if "app" in data else AppConfig()

        # Parse models list
        models_data = data.get("models", [])
        model_configs: List[ModelDefinitionConfig] = []
        for m in models_data:
            if isinstance(m, dict):
                model_configs.append(
                    ModelDefinitionConfig(
                        id=str(m.get("id", "")),
                        provider=str(m.get("provider", "ollama")),
                        capabilities=list(m.get("capabilities", ["general"])),
                        priority=int(m.get("priority", 100)),
                        enabled=bool(m.get("enabled", True)),
                        timeout=float(m["timeout"]) if m.get("timeout") is not None else None,
                        options=dict(m.get("options", {})),
                    )
                )

        # Parse sections
        ollama_cfg = OllamaConfig(**data.get("ollama", {})) if "ollama" in data else OllamaConfig()
        storage_cfg = StorageConfig(**data.get("storage", {})) if "storage" in data else StorageConfig()
        db_cfg = DatabaseConfig(**data.get("database", {})) if "database" in data else DatabaseConfig()
        vs_cfg = VectorStoreConfig(**data.get("vector_store", {})) if "vector_store" in data else VectorStoreConfig()
        emb_cfg = EmbeddingsConfig(**data.get("embeddings", {})) if "embeddings" in data else EmbeddingsConfig()
        vision_cfg = VisionConfig(**data.get("vision", {})) if "vision" in data else VisionConfig()
        rag_cfg = RAGConfig(**data.get("rag", {})) if "rag" in data else RAGConfig()
        agent_cfg = AgentConfig(**data.get("agent", {})) if "agent" in data else AgentConfig()
        sandbox_cfg = SandboxConfig(**data.get("sandbox", {})) if "sandbox" in data else SandboxConfig()
        events_cfg = EventsConfig(**data.get("events", {})) if "events" in data else EventsConfig()
        sec_cfg = SecurityConfig(**data.get("security", {})) if "security" in data else SecurityConfig()
        api_cfg = APIConfig(**data.get("api", {})) if "api" in data else APIConfig()

        return cls(
            app=app_cfg,
            models=model_configs,
            ollama=ollama_cfg,
            storage=storage_cfg,
            database=db_cfg,
            vector_store=vs_cfg,
            embeddings=emb_cfg,
            vision=vision_cfg,
            rag=rag_cfg,
            agent=agent_cfg,
            sandbox=sandbox_cfg,
            events=events_cfg,
            security=sec_cfg,
            api=api_cfg,
        )
