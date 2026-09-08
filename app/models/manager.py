import requests

from .base import BaseModel


class OllamaModel(BaseModel):

    def __init__(
        self,
        model_name: str = "qwen3:4b",
        base_url: str = "http://localhost:11434",
    ):
        self.model_name = model_name
        self.base_url = base_url

    def generate(self, prompt: str) -> str:
        response = requests.post(
            f"{self.base_url}/api/generate",
            json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
            },
        )

        response.raise_for_status()

        return response.json()["response"]


class ModelManager:

    def __init__(self):
        self.model = OllamaModel()

    def generate(self, prompt: str) -> str:
        return self.model.generate(prompt)