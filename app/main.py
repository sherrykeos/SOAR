"""
SOAR Main Application Entry Point.
Initializes the FastAPI application from app.api.create_app().
"""

from app.api import create_app
from app.config import get_config

config = get_config()
app = create_app(config=config)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=config.api.host,
        port=config.api.port,
        reload=config.api.reload,
    )