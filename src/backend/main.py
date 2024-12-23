import asyncio
import json
import logging
import os
import traceback
from typing import Generator

import logfire
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_ipaddr
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse, ServerSentEvent

from backend.agent_search import stream_pro_search_qa
from backend.chat import stream_qa_objects
from backend.db.chat import get_chat_history, get_thread, delete_chat_history
from backend.db.engine import get_session
from backend.schemas import (
    ChatHistoryResponse,
    ChatRequest,
    ChatResponseEvent,
    ErrorStream,
    StreamEvent,
    ThreadResponse,
)
from backend.utils import strtobool
from backend.validators import validate_model

# Load environment variables from .env file
load_dotenv()

# Create a logger instance for logging purposes
logger = logging.getLogger(__name__)


def create_error_event(detail: str) -> ServerSentEvent:
    """
    Creates an error event in the Server-Sent Events (SSE) format.

    Args:
        detail (str): The error message to include in the event.

    Returns:
        ServerSentEvent: An SSE-formatted error event.
    """
    obj = ChatResponseEvent(
        data=ErrorStream(detail=detail),
        event=StreamEvent.ERROR,
    )
    return ServerSentEvent(
        data=json.dumps(jsonable_encoder(obj)),
        event=StreamEvent.ERROR,
    )


def configure_logging(app: FastAPI, logfire_token: str | None):
    """
    Configures logging for the application.

    If a Logfire token is provided, it configures and instruments the FastAPI app with Logfire.

    Args:
        app (FastAPI): The FastAPI application instance.
        logfire_token (str | None): The Logfire token for logging. If None, no logging configuration will be done.
    """
    if logfire_token:
        logfire.configure()
        logfire.instrument_fastapi(app)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> EventSourceResponse:
    """
    Handles rate limit exceeded exceptions by returning an error event in the SSE format.

    Args:
        request (Request): The incoming HTTP request.
        exc (RateLimitExceeded): The exception raised when the rate limit is exceeded.

    Returns:
        EventSourceResponse: An SSE response containing an error event.
    """

    def generator():
        yield create_error_event("Rate limit exceeded, please try again later.")

    return EventSourceResponse(
        generator(),
        media_type="text/event-stream",
    )


def configure_rate_limiting(
    app: FastAPI, rate_limit_enabled: bool, redis_url: str | None
):
    """
    Configures rate limiting for the application.

    Args:
        app (FastAPI): The FastAPI application instance.
        rate_limit_enabled (bool): A flag indicating whether rate limiting should be enabled.
        redis_url (str | None): The Redis URL to use for storing rate limit information. If None, rate limiting will not be enabled.
    """
    limiter = Limiter(
        key_func=get_ipaddr,
        enabled=strtobool(rate_limit_enabled) and redis_url is not None,
        storage_uri=redis_url,
    )
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)  # type: ignore


def configure_middleware(app: FastAPI):
    """
    Configures middleware for the application.

    Adds CORS (Cross-Origin Resource Sharing) middleware to allow requests from any origin.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def create_app() -> FastAPI:
    """
    Creates and configures a new FastAPI application.

    Returns:
        FastAPI: A configured FastAPI application instance.
    """
    app = FastAPI()
    configure_middleware(app)
    configure_logging(app, os.getenv("LOGFIRE_TOKEN"))
    configure_rate_limiting(
        app,
        strtobool(os.getenv("RATE_LIMIT_ENABLED", False)),
        os.getenv("REDIS_URL"),
    )
    return app


# Create the FastAPI application
app = create_app()


@app.post("/chat")
@app.state.limiter.limit("4/min")
async def chat(
    chat_request: ChatRequest, request: Request, session: Session = Depends(get_session)
) -> Generator[ChatResponseEvent, None, None]:
    """
    Handles incoming chat requests.

    Args:
        chat_request (ChatRequest): The chat request data.
        request (Request): The incoming HTTP request.
        session (Session): A database session dependency.

    Returns:
        Generator[ChatResponseEvent, None, None]: A generator yielding chat response events in the SSE format.
    """

    async def generator():
        try:
            validate_model(chat_request.model)
            stream_fn = (
                stream_pro_search_qa if chat_request.pro_search else stream_qa_objects
            )
            async for obj in stream_fn(request=chat_request, session=session):
                if await request.is_disconnected():
                    break
                yield json.dumps(jsonable_encoder(obj))
                await asyncio.sleep(0)
        except Exception as e:
            logger.exception(
                f"Error in chat endpoint: {e}"
            )  # Log the exception properly
            yield create_error_event(str(e))
            await asyncio.sleep(0)
            return

    return EventSourceResponse(generator(), media_type="text/event-stream")  # type: ignore


@app.get("/history")
async def recents(session: Session = Depends(get_session)) -> ChatHistoryResponse:
    """
    Retrieves the chat history.

    Args:
        session (Session): A database session dependency.

    Returns:
        ChatHistoryResponse: The chat history response containing snapshots of past conversations.
    """
    DB_ENABLED = strtobool(os.environ.get("DB_ENABLED", "true"))
    if DB_ENABLED:
        try:
            history = get_chat_history(session=session)
            return ChatHistoryResponse(snapshots=history)
        except Exception as e:
            logger.exception(f"Error fetching chat history: {e}")  # Log the exception
            raise HTTPException(status_code=500, detail=str(e))
    else:
        raise HTTPException(
            status_code=400,
            detail="Chat history is not available when DB is disabled. Please try self-hosting the app by following the instructions here: https://github.com/rashadphz/farfalle",
        )


@app.get("/thread/{thread_id}")
async def thread(
    thread_id: int, session: Session = Depends(get_session)
) -> ThreadResponse:
    """
    Retrieves a specific chat thread.

    Args:
        thread_id (int): The ID of the chat thread to retrieve.
        session (Session): A database session dependency.

    Returns:
        ThreadResponse: The response containing details of the specified chat thread.
    """
    thread = get_thread(session=session, thread_id=thread_id)
    return thread


@app.delete("/history")
async def delete_history(session: Session = Depends(get_session)):
    """
    Deletes the chat history.

    Args:
        session (Session): A database session dependency.

    Returns:
        dict: A response indicating successful deletion of the chat history.
    """
    try:
        logger.info("Attempting to delete chat history...")
        delete_chat_history(session=session)
        logger.info("Chat history deleted successfully.")
        return {"message": "History cleared successfully"}
    except Exception as e:
        logger.exception(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail=f"Error clearing history: {e}")
