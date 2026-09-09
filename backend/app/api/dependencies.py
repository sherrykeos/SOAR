from typing import Optional

from app.config import SOARConfig, get_config, resolve_project_path
from app.database.repository import DatabaseManager
from app.models.manager import ModelManager
from app.orchestrator import Orchestrator, ProgressEventEmitter
from app.storage.local import LocalFileStorage

# Singletons for application lifecycle
_config: Optional[SOARConfig] = None
_db_manager: Optional[DatabaseManager] = None
_storage: Optional[LocalFileStorage] = None
_emitter: Optional[ProgressEventEmitter] = None
_model_manager: Optional[ModelManager] = None
_orchestrator: Optional[Orchestrator] = None


def get_app_config() -> SOARConfig:
    global _config
    if _config is None:
        _config = get_config()
    return _config


def get_db_manager() -> DatabaseManager:
    global _db_manager
    if _db_manager is None:
        cfg = get_app_config()
        resolved_db_path = resolve_project_path(cfg.database.path)
        _db_manager = DatabaseManager(db_path=resolved_db_path)
    return _db_manager


def get_storage() -> LocalFileStorage:
    global _storage
    if _storage is None:
        cfg = get_app_config()
        resolved_storage_root = resolve_project_path(cfg.storage.root)
        db = get_db_manager()
        _storage = LocalFileStorage(
            storage_dir=resolved_storage_root,
            max_file_size_bytes=cfg.storage.max_file_size_bytes,
            allow_empty=cfg.storage.allow_empty,
            db_manager=db,
        )
    return _storage


def get_event_emitter() -> ProgressEventEmitter:
    global _emitter
    if _emitter is None:
        _emitter = ProgressEventEmitter()
    return _emitter


def get_model_manager() -> ModelManager:
    global _model_manager
    if _model_manager is None:
        cfg = get_app_config()
        _model_manager = ModelManager(config=cfg)
    return _model_manager


def get_orchestrator() -> Orchestrator:
    global _orchestrator
    if _orchestrator is None:
        cfg = get_app_config()
        mm = get_model_manager()
        emitter = get_event_emitter()
        _orchestrator = Orchestrator(
            model_manager=mm,
            emitter=emitter,
            max_iterations=cfg.agent.max_iterations,
            config=cfg,
        )
    return _orchestrator


def set_api_dependencies(
    config: Optional[SOARConfig] = None,
    db_manager: Optional[DatabaseManager] = None,
    storage: Optional[LocalFileStorage] = None,
    emitter: Optional[ProgressEventEmitter] = None,
    model_manager: Optional[ModelManager] = None,
    orchestrator: Optional[Orchestrator] = None,
) -> None:
    """Helper to inject or override dependencies (used extensively in test harnesses)."""
    global _config, _db_manager, _storage, _emitter, _model_manager, _orchestrator
    if config is not None:
        _config = config
    if db_manager is not None:
        _db_manager = db_manager
    if storage is not None:
        _storage = storage
    if emitter is not None:
        _emitter = emitter
    if model_manager is not None:
        _model_manager = model_manager
    if orchestrator is not None:
        _orchestrator = orchestrator


def reset_api_dependencies() -> None:
    """Resets all cached dependencies."""
    global _config, _db_manager, _storage, _emitter, _model_manager, _orchestrator
    _config = None
    _db_manager = None
    _storage = None
    _emitter = None
    _model_manager = None
    _orchestrator = None
