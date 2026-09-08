from app.orchestrator.orchestrator import Orchestrator


orchestrator = Orchestrator()

result = orchestrator.run(
    "Read an inspection report and create an approval note"
)

print(result)