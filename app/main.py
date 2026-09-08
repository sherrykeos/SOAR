from fastapi import FastAPI
from pydantic import BaseModel

from app.orchestrator.orchestrator import Orchestrator


app = FastAPI(
    title="SOAR",
    description="Sovereign On-Premise Agentic AI Workbench",
    version="0.1.0",
)

orchestrator = Orchestrator()


class ChatRequest(BaseModel):
    task: str


@app.get("/")
def root():
    return {
        "name": "SOAR",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health") 
def health():
    return {
        "status": "healthy",
    }


@app.post("/chat")
def chat(request: ChatRequest):
    result = orchestrator.run(request.task)

    return {
        "task": result.task,
        "status": result.status,
        "plan": result.plan,
        "results": result.results,
    }