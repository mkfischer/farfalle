## Farfalle Backend: Caching and Content Retrieval

This document details how the Farfalle backend application handles caching, retrieval, and display of search results.

### Caching Mechanism

The application utilizes Redis for caching search results.  The `redis_client` in `search/search_service.py` interacts with the Redis instance, whose URL is configured via the `REDIS_URL` environment variable.

The `perform_search` function in `search/search_service.py` is the central point for search result retrieval.  It first checks the Redis cache using the query as a key (`cache_key = f"search:{query}"`). If a cached result exists, it's deserialized and returned.

If no cached result is found, `perform_search` calls the appropriate `SearchProvider` (determined by the `SEARCH_PROVIDER` environment variable) to fetch the results.  The providers are:

*   `SearxngSearchProvider` (`search/providers/searxng.py`)
*   `TavilySearchProvider` (`search/providers/tavily.py`)
*   `SerperSearchProvider` (`search/providers/serper.py`)
*   `BingSearchProvider` (`search/providers/bing.py`)

After a successful search, the results are serialized and stored in Redis with a 2-hour expiration (`ex=7200`).

### Content Retrieval

The `perform_search` function orchestrates the retrieval process. It attempts to retrieve results from the cache first. If the cache miss occurs, it delegates the search to one of the search providers. Each provider has its own implementation for interacting with the respective search engine API.

### Displaying Cached Content

The cached content is displayed indirectly.  When a user submits a query, the `/chat` endpoint in `main.py` calls `perform_search`.  If a cache hit occurs, the cached results are used to generate the response.  The results are then formatted and streamed to the client via Server-Sent Events (SSE).  The `stream_qa_objects` function in `chat.py` handles this streaming process.  The `SearchResultStream` schema in `schemas.py` defines the structure of the streamed search results.

### Cache Terms

*   **Cache Key:**  `"search:{query}"` where `{query}` is the user's search query.
*   **Expiration:** 2 hours (7200 seconds).
*   **Storage:** Redis, configured via the `REDIS_URL` environment variable.
*   **Cache Invalidation:**  The cache is automatically invalidated after 2 hours.  There's no explicit cache invalidation mechanism beyond the expiration time.


### Classes and Methods Summary

| File                     | Class/Method          | Description                                                                     |
| ------------------------ | --------------------- | ------------------------------------------------------------------------------- |
| `search/search_service.py` | `perform_search`      | Main function for search result retrieval, cache handling.                     |
| `search/search_service.py` | `get_search_provider` | Selects the appropriate search provider based on environment variables.        |
| `search/providers/*.py`   | `SearchProvider`      | Abstract base class for search providers.                                      |
| `search/providers/*.py`   | Provider implementations | Specific implementations for different search engines (Searxng, Tavily, Serper, Bing). |
| `chat.py`                | `stream_qa_objects`   | Streams search results and other data to the client.                           |
| `schemas.py`             | `SearchResult`         | Pydantic model for representing a single search result.                         |
| `schemas.py`             | `SearchResponse`       | Pydantic model for representing the overall search response.                    |
| `main.py`                | `/chat` endpoint       | FastAPI endpoint handling user queries and responses.                          |


This comprehensive overview clarifies the caching strategy and data flow within the Farfalle backend.  The system prioritizes efficiency by leveraging Redis for caching and employs a flexible architecture to support multiple search providers.
