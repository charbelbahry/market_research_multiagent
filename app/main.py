from fastapi import FastAPI
from app.config import get_settings
from app.api.routes import router


def create_app() -> FastAPI:
    settings = get_settings()

    if settings.langfuse_public_key and settings.langfuse_secret_key:
        import os

        os.environ["LANGFUSE_PUBLIC_KEY"] = settings.langfuse_public_key
        os.environ["LANGFUSE_SECRET_KEY"] = settings.langfuse_secret_key
        os.environ["LANGFUSE_HOST"] = settings.langfuse_host

        try:
            from langfuse import get_client

            langfuse = get_client()

            from app.utils.logging import get_logger

            logger = get_logger(__name__)

            if langfuse.auth_check():
                import openlit

                openlit.init(application_name=settings.app_name)
                logger.info(
                    "Langfuse client authenticated and OpenLit initialized successfully."
                )
            else:
                logger.error(
                    "Langfuse authentication failed. Please check your credentials and host."
                )

        except Exception as e:
            from app.utils.logging import get_logger

            logger = get_logger(__name__)
            logger.error(f"Failed to initialize OpenLit for Langfuse: {e}")

    app = FastAPI(title=settings.app_name)
    app.include_router(router)
    return app


app = create_app()
