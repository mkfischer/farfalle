## Farfalle Backend Architecture Documentation

This document details the backend architecture of the Farfalle application, focusing on prompt handling and the flow from prompt to response, both in normal and expert modes.

**I. Core Components:**

The backend is built using FastAPI, SQLAlchemy, and several external libraries for LLM interaction and search.  Key components include:

* **`main.py`**: The FastAPI application entry point.  Handles routing, dependency injection, rate limiting, and error handling.  It uses `stream_qa_objects` for normal mode and `stream_pro_search_qa` for expert mode.  It also includes endpoints for retrieving chat history (`/history`) and individual threads (`/thread/{thread_id}`).

* **`chat.py`**: Contains the core logic for handling chat requests.  The `stream_qa_objects` asynchronous generator handles the standard chat flow, while `stream_pro_search_qa` handles the expert search flow.  It uses `rephrase_query_with_history` to refine queries based on chat history and `format_context` to prepare search results for the LLM.

* **`agent_search.py`**: Implements the expert search mode.  `stream_pro_search_qa` orchestrates the process, leveraging `stream_pro_search_objects` to manage query planning, search execution, and result aggregation.  It uses several helper functions to manage the steps of the expert search.

* **`llm/base.py`**: Defines the abstract `BaseLLM` class and its concrete implementation `EveryLLM`.  `EveryLLM` uses the `litellm` library to interact with various LLMs (OpenAI, LlamaIndex, etc.), providing methods for streaming (`astream`), single-shot completion (`complete`), and structured completion (`structured_complete`).

* **`related_queries.py`**: Contains the `generate_related_queries` function, which uses an LLM to generate follow-up questions based on the initial query and search results.

* **`search/search_service.py`**:  Handles search requests.  `perform_search` uses a configurable search provider (`get_search_provider`) to execute searches and caches results using Redis (if configured).

* **`search/providers/base.py`**: Defines the abstract `SearchProvider` class.

* **`search/providers/{provider}.py`**:  Implementations for different search providers (Bing, SearxNG, Serper, Tavily). Each provider implements the `search` method to interact with its respective API.

* **`db/models.py`**: Defines SQLAlchemy models for database interaction (`ChatThread`, `ChatMessage`, `SearchResult`).

* **`db/engine.py`**: Configures the SQLAlchemy engine and provides a session factory (`get_session`).

* **`db/chat.py`**: Contains database functions for managing chat threads, messages, and search results (`create_chat_thread`, `append_message`, `save_turn_to_db`, `get_chat_history`, `get_thread`).

* **`schemas.py`**: Defines Pydantic models for data serialization and validation (`ChatRequest`, `ChatResponseEvent`, `SearchResult`, etc.).

* **`constants.py`**: Defines constants and enums used throughout the application, including `ChatModel` which specifies the different LLMs that can be used.

* **`utils.py`**: Contains utility functions, including `is_local_model` and `strtobool`.

* **`prompts.py`**: Contains the prompt templates used for LLM interaction (`CHAT_PROMPT`, `RELATED_QUESTION_PROMPT`, `HISTORY_QUERY_REPHRASE`, `QUERY_PLAN_PROMPT`, `SEARCH_QUERY_PROMPT`).

* **`validators.py`**: Contains validation functions, including `validate_model` which checks for API keys and model availability.


**II. Prompt Handling and Response Flow:**

**A. Normal Mode:**

1. A `ChatRequest` is received by the `/chat` endpoint in `main.py`.
2. `main.py` calls `stream_qa_objects` in `chat.py`.
3. `rephrase_query_with_history` in `chat.py` refines the query using chat history and the LLM.
4. `perform_search` in `search/search_service.py` performs a search using the selected provider.
5. `format_context` in `chat.py` prepares the search results for the LLM.
6. `CHAT_PROMPT` in `prompts.py` is used to construct the prompt for the LLM.
7. `EveryLLM.astream` in `llm/base.py` streams the LLM response.
8. Results are streamed back to the client as `ChatResponseEvent` objects.
9. `generate_related_queries` in `related_queries.py` generates follow-up questions.
10. The chat turn is saved to the database using `save_turn_to_db` in `db/chat.py`.


**B. Expert Mode:**

1. A `ChatRequest` with `pro_search=True` is received by the `/chat` endpoint in `main.py`.
2. `main.py` calls `stream_pro_search_qa` in `agent_search.py`.
3. `rephrase_query_with_history` in `chat.py` refines the query.
4. `stream_pro_search_objects` in `agent_search.py` is called.
5. `QUERY_PLAN_PROMPT` in `prompts.py` is used to generate a query plan.
6. The query plan is executed step-by-step.  Each step involves:
    * Generating search queries using `SEARCH_QUERY_PROMPT` in `prompts.py`.
    * Performing searches using `perform_search`.
    * Streaming search results to the client.
    * Building context from previous steps.
7. Finally, the aggregated context is used to construct a prompt using `CHAT_PROMPT`.
8. The LLM response is streamed back to the client.
9. The chat turn is saved to the database.


**III. Database Interactions:**

The application uses a PostgreSQL database to store chat history.  The `db/models.py` file defines the database schema, and the `db/chat.py` file provides functions for interacting with the database.  The database schema includes tables for chat threads, messages, and search results.


**IV. Error Handling:**

The application includes comprehensive error handling throughout the codebase.  Errors are caught and handled gracefully, with appropriate HTTP status codes and error messages returned to the client.  Logging is also implemented to track errors and other relevant events.


This documentation provides a high-level overview of the Farfalle backend architecture.  For more detailed information, refer to the individual source code files.
