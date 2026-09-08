from fastapi import FastAPI

app = FastAPI(
    title="Vajra",
    description="Sovereign On-Premise Agentic AI Workbench",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "Vajra",
        "status": "online",
        "version": "0.1.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
    }