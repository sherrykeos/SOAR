import json
import requests
from typing import Any, Set

from .adapter import ModelAdapter, ModelCapability, ModelMetadata


class OllamaModel(ModelAdapter):

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
        base_url: str = "http://localhost:11434",
        capabilities: Set[str] | None = None,
        priority: int = 10,
        timeout: int | float = 180,
    ):
        self._model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._capabilities = capabilities or {
            ModelCapability.GENERAL,
            ModelCapability.REASONING,
        }
        self._priority = priority
        self.timeout = timeout

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self._model_name,
            provider="ollama",
            capabilities=self._capabilities,
            priority=self._priority,
        )

    _tags_cache = None
    _tags_cache_time = 0.0

    def is_available(self) -> bool:
        """
        Checks whether the model is actually installed and available in the local Ollama instance.
        100% local check via /api/tags without cloud access.
        Caches tags response briefly (3s) to avoid redundant serial HTTP roundtrips when listing multiple models.
        """
        import time

        now = time.time()
        installed_names = None
        if OllamaModel._tags_cache is not None and (now - OllamaModel._tags_cache_time) < 3.0:
            installed_names = OllamaModel._tags_cache
        else:
            try:
                resp = requests.get(f"{self.base_url}/api/tags", timeout=1.5)
                if resp.status_code == 200:
                    models = resp.json().get("models", [])
                    installed_names = [m.get("name", "").lower() for m in models]
                    OllamaModel._tags_cache = installed_names
                    OllamaModel._tags_cache_time = now
            except Exception:
                pass

        if installed_names is None:
            return False

        target = self._model_name.lower()
        return any(
            target == name or target.split(":")[0] == name.split(":")[0]
            for name in installed_names
        )

    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
        timeout: int | float | None = None,
        **kwargs: Any,
    ) -> str:
        eff_timeout = timeout if timeout is not None else self.timeout
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self._model_name,
                    "prompt": prompt,
                    "stream": True,
                    "think": think,
                },
                stream=True,
                timeout=eff_timeout,
            )
            response.raise_for_status()
        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                f"Ollama model '{self._model_name}' timed out after {eff_timeout} seconds."
            ) from e
        except requests.exceptions.ConnectionError as e:
            raise ConnectionError(
                f"Could not connect to Ollama server at '{self.base_url}'. "
                "Please make sure Ollama is installed and running (run 'ollama serve' or open the Ollama application)."
            ) from e
        except requests.exceptions.HTTPError as e:
            raise RuntimeError(
                f"Ollama returned HTTP error {response.status_code}: {response.text}. "
                f"Ensure the model '{self._model_name}' is downloaded using 'ollama pull {self._model_name}'."
            ) from e

        chunks = []

        for line in response.iter_lines():
            if not line:
                continue

            data = json.loads(line)
            chunk = data.get("response", "")
            if chunk:
                chunks.append(chunk)

        return "".join(chunks)
