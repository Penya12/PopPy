"""Skeleton setup required for the fastAPI app."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from poppy.api.routes.events import router as events_router
from poppy.db.session import DATABASE_URL, ENGINE, init_db_engine_and_sessionmaker


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None, None]:  # noqa: ARG001
    """Similar to typer callback, this sets up and tears down the DB engine."""
    # In async context manager, the part before yield is run before entering
    # the with block, and the part after yield is run after exiting the with block.
    init_db_engine_and_sessionmaker(DATABASE_URL)
    yield
    if ENGINE is not None:
        ENGINE.dispose()


# FastAPI will do the equivalent of calling `with lifespan(app):` when using every endpoint
app = FastAPI(title="PopPy API", lifespan=lifespan)
app.include_router(events_router)


@app.get("/")
def read_root() -> dict[str, str]:
    """Meant to be hit to check if the API is alive."""
    return {"Poppy": "Your Popeye-powered secretary"}
