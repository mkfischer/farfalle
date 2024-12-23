from backend.llm.base import BaseLLM
from backend.prompts import RELATED_QUESTION_PROMPT
from backend.schemas import RelatedQueries, SearchResult


async def generate_related_queries(
    query: str, search_results: list[SearchResult], llm: BaseLLM
) -> list[str]:
    """
    Generates related queries based on an initial query and search results using a language model.

    Args:
        query: The initial query string.
        search_results: A list of SearchResult objects representing the search results.
        llm: An instance of BaseLLM for interacting with the language model.

    Returns:
        A list of related query strings.  The question marks are removed and the queries are lowercased.
    """
    context = "\n\n".join([f"{str(result)}" for result in search_results])
    context = context[:4000]
    related = llm.structured_complete(
        RelatedQueries, RELATED_QUESTION_PROMPT.format(query=query, context=context)
    )
    return [query.lower().replace("?", "") for query in related.related_questions]
