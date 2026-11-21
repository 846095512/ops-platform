from fastapi import FastAPI

from src.core.contextmanager import combined_lifespan
from src.core.exception import setup_exception_handlers
from src.core.logger import setup_logging
from src.core.middleware import api_logging_middleware, api_auth_middleware
from src.routers.user_router import router as user_router

setup_logging()
app = FastAPI(lifespan=combined_lifespan)

app.middleware("http")(api_logging_middleware)
app.middleware("http")(api_auth_middleware)
app.include_router(user_router, prefix="/api/v1")

# register global exception handlers
setup_exception_handlers(app)
