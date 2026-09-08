import json
import requests

from .base import BaseModel


class OllamaModel(BaseModel):

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
        base_url: str = "http://localhost:11434",
    ):
        self.model_name = model_name
        self.base_url = base_url

    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
    ) -> str:

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
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
                f"Ensure the model '{self.model_name}' is downloaded using 'ollama pull {self.model_name}'."
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


class ModelManager:

    def __init__(
        self,
        model_name: str = "qwen3:1.7b",
    ):
        self.model = OllamaModel(
            model_name=model_name,
        )

    def generate(
        self,
        prompt: str,
        *,
        think: bool = False,
    ) -> str:

        return self.model.generate(
            prompt,
            think=think,
        )