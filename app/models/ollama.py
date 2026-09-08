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
    ):
        self._model_name = model_name
        self.base_url = base_url.rstrip("/")
        self._capabilities = capabilities or {
            ModelCapability.GENERAL,
            ModelCapability.REASONING,
        }
        self._priority = priority

    @property
    def metadata(self) -> ModelMetadata:
        return ModelMetadata(
            model_id=self._model_name,
            provider="ollama",
            capabilities=self._capabilities,
            priority=self._priority,
        )

    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
        **kwargs: Any,
    ) -> str:
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
                timeout=180,
            )
            response.raise_for_status()
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
