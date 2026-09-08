from app.models.manager import ModelManager


model_manager = ModelManager()

response = model_manager.generate(
    "Explain what an industrial inspection report is in two sentences."
)

print(response)