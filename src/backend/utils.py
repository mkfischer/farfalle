import os
from backend.constants import ChatModel


def is_local_model(model: ChatModel) -> bool:
    """
    Checks if a given ChatModel is a local model.

    Args:
        model: The ChatModel to check.

    Returns:
        True if the model is a local model, False otherwise.
    """
    return model in [
        ChatModel.LOCAL_LLAMA_3,
        ChatModel.LOCAL_GEMMA,
        ChatModel.LOCAL_MISTRAL,
        ChatModel.LOCAL_PHI3_14B,
        ChatModel.CUSTOM,
    ]


def strtobool(val: str | bool) -> bool:
    """
    Converts a string or boolean value to a boolean.

    Args:
        val: The string or boolean value to convert.

    Returns:
        True if the value is True, 1, t, or "true", False otherwise.
    """
    if isinstance(val, bool):
        return val
    return val.lower() in ("true", "1", "t")


DB_ENABLED = strtobool(os.environ.get("DB_ENABLED", "true"))
PRO_MODE_ENABLED = strtobool(os.environ.get("PRO_MODE_ENABLED", "true"))
