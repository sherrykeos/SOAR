import logging
import os
from pathlib import Path
from typing import Any, Dict, Optional, Set

import yaml

from app.models.adapter import ModelCapability

from .schema import (
    AppConfig,
    ModelDefinitionConfig,
    SOARConfig,
)

logger = logging.getLogger(__name__)

# Valid model capabilities defined in the system
VALID_CAPABILITIES: Set[str] = {
    ModelCapability.GENERAL,
    ModelCapability.REASONING,
    ModelCapability.CODING,
    ModelCapability.VISION,
    ModelCapability.DOCUMENT,
}

# Supported model backend providers
SUPPORTED_PROVIDERS: Set[str] = {"ollama", "mock"}


class ConfigError(Exception):
    """Base exception for SOAR configuration errors."""
    pass


class ConfigFileNotFoundError(ConfigError):
    """Raised when a specified configuration file does not exist."""
    pass


class ConfigParsingError(ConfigError):
    """Raised when configuration YAML syntax is malformed."""
    pass


class ConfigValidationError(ConfigError):
    """Raised when configuration values fail validation rules."""
    pass


def get_project_root() -> Path:
    """
    Returns the root directory of the SOAR project.
    Determined by navigating upwards until directory containing 'app' and 'config' is found.
    """
    current = Path(__file__).resolve().parent
    for parent in [current, *current.parents]:
        if (parent / "app").is_dir() and (parent / "config").is_dir():
            return parent
        if (parent / "app").is_dir() and (parent / "data").is_dir():
            return parent

    # Fallback to parent of 'app' directory
    return Path(__file__).resolve().parent.parent.parent


def resolve_project_path(path_str: str | Path, project_root: Optional[Path] = None) -> Path:
    """
    Resolves a path string relative to the SOAR project root if relative.
    Absolute paths are preserved as-is.
    """
    p = Path(path_str)
    if p.is_absolute():
        return p

    root = project_root or get_project_root()
    return (root / p).resolve()


def validate_config(config: SOARConfig) -> None:
    """
    Performs comprehensive validation on a SOARConfig instance.
    Raises ConfigValidationError on invalid settings.
    """
    # 1. Validate models
    seen_model_ids: Set[str] = set()
    for idx, model in enumerate(config.models):
        if not model.id or not model.id.strip():
            raise ConfigValidationError(f"models[{idx}]: 'id' must be a non-empty string.")

        model_id = model.id.strip()
        if model_id in seen_model_ids:
            raise ConfigValidationError(f"models[{idx}]: Duplicate model ID '{model_id}' detected.")
        seen_model_ids.add(model_id)

        # Validate provider
        if model.provider.lower() not in SUPPORTED_PROVIDERS:
            raise ConfigValidationError(
                f"models[{idx}] ('{model_id}'): Unsupported provider '{model.provider}'. "
                f"Supported providers: {sorted(list(SUPPORTED_PROVIDERS))}"
            )

        # Validate capabilities against existing ModelCapability constants
        if not model.capabilities:
            raise ConfigValidationError(
                f"models[{idx}] ('{model_id}'): Model must have at least one capability specified."
            )

        for cap in model.capabilities:
            if cap.lower() not in VALID_CAPABILITIES:
                raise ConfigValidationError(
                    f"models[{idx}] ('{model_id}'): Invalid capability '{cap}'. "
                    f"Allowed capabilities: {sorted(list(VALID_CAPABILITIES))}"
                )

        # Validate numeric limits
        if model.priority < 0:
            raise ConfigValidationError(
                f"models[{idx}] ('{model_id}'): 'priority' must be a non-negative integer (got {model.priority})."
            )

        if model.timeout is not None and model.timeout <= 0:
            raise ConfigValidationError(
                f"models[{idx}] ('{model_id}'): 'timeout' must be a positive number (got {model.timeout})."
            )

    # 2. Validate Storage
    if config.storage.max_file_size_bytes <= 0:
        raise ConfigValidationError(
            f"storage.max_file_size_bytes must be greater than 0 (got {config.storage.max_file_size_bytes})."
        )

    # 3. Validate RAG
    if config.rag.top_k <= 0:
        raise ConfigValidationError(f"rag.top_k must be greater than 0 (got {config.rag.top_k}).")
    if config.rag.chunk_size <= 0:
        raise ConfigValidationError(f"rag.chunk_size must be greater than 0 (got {config.rag.chunk_size}).")
    if config.rag.chunk_overlap < 0:
        raise ConfigValidationError(f"rag.chunk_overlap must be non-negative (got {config.rag.chunk_overlap}).")
    if config.rag.chunk_overlap >= config.rag.chunk_size:
        raise ConfigValidationError(
            f"rag.chunk_overlap ({config.rag.chunk_overlap}) cannot be greater than or equal to "
            f"rag.chunk_size ({config.rag.chunk_size})."
        )

    # 4. Validate Agent
    if config.agent.max_iterations <= 0:
        raise ConfigValidationError(
            f"agent.max_iterations must be greater than 0 (got {config.agent.max_iterations})."
        )
    if config.agent.hard_model_timeout <= 0:
        raise ConfigValidationError(
            f"agent.hard_model_timeout must be greater than 0 (got {config.agent.hard_model_timeout})."
        )

    # 5. Validate Sandbox
    if config.sandbox.timeout <= 0:
        raise ConfigValidationError(
            f"sandbox.timeout must be greater than 0 (got {config.sandbox.timeout})."
        )

    # 6. Validate Ollama / Vision
    if config.ollama.timeout <= 0:
        raise ConfigValidationError(
            f"ollama.timeout must be greater than 0 (got {config.ollama.timeout})."
        )
    if config.vision.timeout <= 0:
        raise ConfigValidationError(
            f"vision.timeout must be greater than 0 (got {config.vision.timeout})."
        )


def load_config(config_path: Optional[str | Path] = None) -> SOARConfig:
    """
    Loads, parses, resolves paths, and validates SOAR configuration from YAML.

    Lookup hierarchy:
    1. Explicit config_path argument
    2. SOAR_CONFIG_PATH environment variable
    3. <project_root>/config/config.yaml
    4. Fallback to default SOARConfig if file does not exist
    """
    project_root = get_project_root()

    if config_path is not None:
        target_file = Path(config_path)
        if not target_file.is_absolute():
            target_file = (project_root / target_file).resolve()
        if not target_file.exists():
            raise ConfigFileNotFoundError(f"Configuration file not found at: '{target_file}'")
    else:
        env_path = os.environ.get("SOAR_CONFIG_PATH")
        if env_path:
            target_file = Path(env_path)
            if not target_file.is_absolute():
                target_file = (project_root / target_file).resolve()
            if not target_file.exists():
                raise ConfigFileNotFoundError(f"Configuration file from SOAR_CONFIG_PATH not found at: '{target_file}'")
        else:
            target_file = project_root / "config" / "config.yaml"

    if not target_file.exists():
        logger.info(f"No configuration file found at '{target_file}'. Using default SOAR configuration.")
        config = SOARConfig()
        validate_config(config)
        return config

    try:
        raw_text = target_file.read_text(encoding="utf-8")
        parsed_dict = yaml.safe_load(raw_text) or {}
    except yaml.YAMLError as e:
        raise ConfigParsingError(f"Failed to parse YAML configuration in '{target_file}': {str(e)}") from e
    except Exception as e:
        raise ConfigError(f"Error reading configuration file '{target_file}': {str(e)}") from e

    config = SOARConfig.from_dict(parsed_dict)
    validate_config(config)
    return config


# Global cached config instance
_GLOBAL_CONFIG: Optional[SOARConfig] = None


def get_config() -> SOARConfig:
    """Returns the active global SOARConfig, loading it on first access."""
    global _GLOBAL_CONFIG
    if _GLOBAL_CONFIG is None:
        _GLOBAL_CONFIG = load_config()
    return _GLOBAL_CONFIG


def set_config(config: SOARConfig) -> None:
    """Overrides the active global SOARConfig (primarily for test harnesses)."""
    global _GLOBAL_CONFIG
    validate_config(config)
    _GLOBAL_CONFIG = config


def reset_config() -> None:
    """Resets global cached config to None."""
    global _GLOBAL_CONFIG
    _GLOBAL_CONFIG = None
