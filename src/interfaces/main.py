from src.interfaces.api.main import create_api_app
from src.infrastructure.settings import Settings, get_settings
import uvicorn


settings: Settings = get_settings()
app = create_api_app()


if __name__ == "__main__":
    uvicorn.run(
        "src.interfaces.main:app",
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.debug,
        log_level="debug" if settings.api.debug else "info",
        use_colors=True,
    )