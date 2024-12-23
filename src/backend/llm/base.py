import os
from abc import ABC, abstractmethod
import instructor
from dotenv import load_dotenv
from instructor.client import T
from litellm import completion
from litellm.utils import validate_environment
from llama_index.core.base.llms.types import (
    CompletionResponse,
    CompletionResponseAsyncGen,
)
from llama_index.llms.litellm import LiteLLM

# Load environment variables from .env file
load_dotenv()


class BaseLLM(ABC):
    """
    Abstract base class for all LLMs.
    """

    @abstractmethod
    async def astream(self, prompt: str) -> CompletionResponseAsyncGen:
        """
        Streams the completion of a given prompt.

        Args:
            prompt: The prompt to complete.

        Returns:
            An asynchronous generator yielding CompletionResponseAsyncGen objects.
        """
        pass

    @abstractmethod
    def complete(self, prompt: str) -> CompletionResponse:
        """
        Completes a given prompt.

        Args:
            prompt: The prompt to complete.

        Returns:
            A CompletionResponse object.
        """
        pass

    @abstractmethod
    def structured_complete(self, response_model: type[T], prompt: str) -> T:
        """
        Completes a given prompt and structures the response using a given Pydantic model.

        Args:
            response_model: The Pydantic model to structure the response with.
            prompt: The prompt to complete.

        Returns:
            An object of type T.
        """
        pass


class EveryLLM(BaseLLM):
    """
    A concrete implementation of the BaseLLM abstract base class that uses LiteLLM.
    """

    def __init__(
        self,
        model: str,
    ):
        """
        Initializes the EveryLLM class.

        Args:
            model: The name of the LLM model to use.
        """
        # Set default Ollama API base URL
        os.environ.setdefault("OLLAMA_API_BASE", "http://localhost:11434")
        # Validate environment variables
        validation = validate_environment(model)
        if validation["missing_keys"]:
            raise ValueError(f"Missing keys: {validation['missing_keys']}")
        # Initialize LiteLLM
        self.llm = LiteLLM(model=model)
        # Initialize instructor client, handling different modes based on the model
        if "groq" in model or "ollama_chat" in model:
            self.client = instructor.from_litellm(
                completion, mode=instructor.Mode.MD_JSON
            )
        else:
            self.client = instructor.from_litellm(completion)

    async def astream(self, prompt: str) -> CompletionResponseAsyncGen:
        """
        Streams the completion of a given prompt using LiteLLM.

        Args:
            prompt: The prompt to complete.

        Returns:
            An asynchronous generator yielding CompletionResponseAsyncGen objects.
        """
        return await self.llm.astream_complete(prompt)

    def complete(self, prompt: str) -> CompletionResponse:
        """
        Completes a given prompt using LiteLLM.

        Args:
            prompt: The prompt to complete.

        Returns:
            A CompletionResponse object.
        """
        return self.llm.complete(prompt)

    def structured_complete(self, response_model: type[T], prompt: str) -> T:
        """
        Completes a given prompt using instructor and structures the response using a given Pydantic model.

        Args:
            response_model: The Pydantic model to structure the response with.
            prompt: The prompt to complete.

        Returns:
            An object of type T.
        """
        return self.client.chat.completions.create(
            model=self.llm.model,
            messages=[{"role": "user", "content": prompt}],
            response_model=response_model,
        )
