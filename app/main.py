from fastapi import FastAPI
from app.config import get_settings
from app.api.routes import router


def create_app() -> FastAPI:
    settings = get_settings()

    # Initialize Langfuse Observability
    if settings.langfuse_public_key and settings.langfuse_secret_key:
        import os
        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host
        
        try:
            import openlit
            openlit.init(application_name=settings.app_name)
        except Exception as e:
            from app.utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(f"Failed to initialize OpenLit for Langfuse: {e}")

    app = FastAPI(title=settings.app_name)
    app.include_router(router)
    return app


app = create_app()
