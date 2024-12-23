# Some of the code here is based on github.com/cohere-ai/cohere-toolkit/
import os
from datetime import datetime
from enum import Enum
from typing import List, Union

from dotenv import load_dotenv
from logfire.integrations.pydantic import PluginSettings
from pydantic import BaseModel, Field

from backend.constants import ChatModel
from backend.utils import strtobool

load_dotenv()

record_all = PluginSettings(logfire={"record": "all"})


class MessageRole(str, Enum):
    """
    Represents the role of a message in a chat conversation.

    USER: Message sent by the user.
    ASSISTANT: Message sent by the AI assistant.
    """

    USER = "user"
    ASSISTANT = "assistant"


class Message(BaseModel):
    """
    Represents a single message in a chat conversation.
    """

    content: str
    """The text content of the message."""
    role: MessageRole
    """The role of the message sender (user or assistant)."""


LOCAL_MODELS_ENABLED = strtobool(os.getenv("ENABLE_LOCAL_MODELS", False))


class ChatRequest(BaseModel, plugin_settings=record_all):
    """
    Represents a request to the chat API.
    """

    thread_id: int | None = None
    """The ID of the chat thread (optional)."""
    query: str
    """The user's query or message."""
    history: List[Message] = Field(default_factory=list)
    """The chat history."""
    model: ChatModel = ChatModel.GPT_4o_mini
    """The language model to use."""
    pro_search: bool = False
    """Whether to enable professional search."""


class RelatedQueries(BaseModel):
    """
    Represents a list of related queries.
    """

    related_questions: List[str] = Field(..., min_length=3, max_length=3)
    """A list of related questions (minimum 3, maximum 3)."""


class SearchResult(BaseModel):
    """
    Represents the result of a search query.
    """

    title: str
    """The title of the search result."""
    url: str
    """The URL of the search result."""
    content: str
    """A summary of the search result content."""

    def __str__(self):
        return f"Title: {self.title}\nURL: {self.url}\n Summary: {self.content}"


class SearchResponse(BaseModel):
    """
    Represents a response containing search results and images.
    """

    results: List[SearchResult] = Field(default_factory=list)
    """A list of search results."""
    images: List[str] = Field(default_factory=list)
    """A list of image URLs."""


class AgentSearchStepStatus(str, Enum):
    """
    Represents the status of an agent search step.

    DONE: The step is completed.
    CURRENT: The step is currently being processed.
    DEFAULT: The default status.
    """

    DONE = "done"
    CURRENT = "current"
    DEFAULT = "default"


class AgentSearchStep(BaseModel):
    """
    Represents a single step in an agent's search process.
    """

    step_number: int
    """The step number."""
    step: str
    """A description of the step."""
    queries: List[str] = Field(default_factory=list)
    """The queries executed in this step."""
    results: List[SearchResult] = Field(default_factory=list)
    """The results obtained in this step."""
    status: AgentSearchStepStatus = AgentSearchStepStatus.DEFAULT
    """The status of the step."""


class AgentSearchFullResponse(BaseModel):
    """
    Represents the complete response from an agent search.
    """

    steps: list[str] = Field(default_factory=list)
    """A list of steps."""
    steps_details: List[AgentSearchStep] = Field(default_factory=list)
    """Detailed information about each step."""


class StreamEvent(str, Enum):
    """
    Represents different events in a streaming response.
    """

    BEGIN_STREAM = "begin-stream"
    SEARCH_RESULTS = "search-results"
    TEXT_CHUNK = "text-chunk"
    RELATED_QUERIES = "related-queries"
    STREAM_END = "stream-end"
    FINAL_RESPONSE = "final-response"
    ERROR = "error"
    # Agent Events
    AGENT_QUERY_PLAN = "agent-query-plan"
    AGENT_SEARCH_QUERIES = "agent-search-queries"
    AGENT_READ_RESULTS = "agent-read-results"
    AGENT_FINISH = "agent-finish"
    AGENT_FULL_RESPONSE = "agent-full-response"


class ChatObject(BaseModel):
    """
    Base class for chat objects in a streaming response.
    """

    event_type: StreamEvent
    """The type of event."""


class BeginStream(ChatObject, plugin_settings=record_all):
    """
    Represents the beginning of a stream event.
    """

    event_type: StreamEvent = StreamEvent.BEGIN_STREAM
    query: str
    """The user's query."""


class SearchResultStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing search results.
    """

    event_type: StreamEvent = StreamEvent.SEARCH_RESULTS
    results: List[SearchResult] = Field(default_factory=list)
    """A list of search results."""
    images: List[str] = Field(default_factory=list)
    """A list of image URLs."""


class TextChunkStream(ChatObject):
    """
    Represents a stream event containing a chunk of text.
    """

    event_type: StreamEvent = StreamEvent.TEXT_CHUNK
    text: str
    """A chunk of text."""


class RelatedQueriesStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing related queries.
    """

    event_type: StreamEvent = StreamEvent.RELATED_QUERIES
    related_queries: List[str] = Field(default_factory=list)
    """A list of related queries."""


class StreamEndStream(ChatObject, plugin_settings=record_all):
    """
    Represents the end of a stream event.
    """

    thread_id: int | None = None
    event_type: StreamEvent = StreamEvent.STREAM_END


class FinalResponseStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing the final response.
    """

    event_type: StreamEvent = StreamEvent.FINAL_RESPONSE
    message: str
    """The final response message."""


class ErrorStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing an error.
    """

    event_type: StreamEvent = StreamEvent.ERROR
    detail: str
    """The error details."""


class AgentQueryPlanStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing an agent's query plan.
    """

    event_type: StreamEvent = StreamEvent.AGENT_QUERY_PLAN
    steps: List[str] = Field(default_factory=list)
    """A list of steps in the query plan."""


class AgentSearchQueriesStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing an agent's search queries.
    """

    event_type: StreamEvent = StreamEvent.AGENT_SEARCH_QUERIES
    step_number: int
    """The step number."""
    queries: List[str] = Field(default_factory=list)
    """A list of search queries."""


class AgentReadResultsStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing an agent's search results.
    """

    event_type: StreamEvent = StreamEvent.AGENT_READ_RESULTS
    step_number: int
    """The step number."""
    results: List[SearchResult] = Field(default_factory=list)
    """A list of search results."""


class AgentSearchFullResponseStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event containing a full agent search response.
    """

    event_type: StreamEvent = StreamEvent.AGENT_FULL_RESPONSE
    response: AgentSearchFullResponse
    """The full agent search response."""


class AgentFinishStream(ChatObject, plugin_settings=record_all):
    """
    Represents a stream event indicating the agent has finished.
    """

    event_type: StreamEvent = StreamEvent.AGENT_FINISH


class ChatResponseEvent(BaseModel):
    """
    Represents a chat response event.
    """

    event: StreamEvent
    """The type of event."""
    data: Union[
        BeginStream,
        SearchResultStream,
        TextChunkStream,
        RelatedQueriesStream,
        StreamEndStream,
        FinalResponseStream,
        ErrorStream,
        AgentQueryPlanStream,
        AgentSearchQueriesStream,
        AgentReadResultsStream,
        AgentFinishStream,
        AgentSearchFullResponseStream,
    ]
    """The event data."""


class ChatSnapshot(BaseModel):
    """
    Represents a snapshot of a chat conversation.
    """

    id: int
    """The ID of the snapshot."""
    title: str
    """The title of the snapshot."""
    date: datetime
    """The date and time of the snapshot."""
    preview: str
    """A preview of the conversation."""
    model_name: str
    """The name of the language model used."""


class ChatHistoryResponse(BaseModel):
    """
    Represents a response containing chat history snapshots.
    """

    snapshots: List[ChatSnapshot] = Field(default_factory=list)
    """A list of chat snapshots."""


class ChatMessage(BaseModel):
    """
    Represents a single message in a chat conversation.
    """

    content: str
    """The content of the message."""
    role: MessageRole
    """The role of the sender."""
    related_queries: List[str] | None = None
    """Related queries."""
    sources: List[SearchResult] | None = None
    """Sources used to generate the message."""
    images: List[str] | None = None
    """Images associated with the message."""
    is_error_message: bool = False
    """Indicates if the message is an error message."""
    agent_response: AgentSearchFullResponse | None = None
    """Agent search response."""


class ThreadResponse(BaseModel):
    """
    Represents a response containing a chat thread.
    """

    thread_id: int
    """The ID of the thread."""
    messages: List[ChatMessage] = Field(default_factory=list)
    """A list of messages in the thread."""
