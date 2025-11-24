from enum import Enum
from typing import Literal


class AnthropicStopReason(str, Enum):
    """
    Enum for Anthropic API stop_reason values.
    Reference: https://docs.anthropic.com/en/api/messages

    Values:
    - END_TURN: Model completed its turn naturally
    - MAX_TOKENS: Hit max_tokens limit
    - TOOL_USE: Model wants to use a tool
    - STOP_SEQUENCE: Hit a stop sequence (if configured)
    """

    END_TURN = "end_turn"
    MAX_TOKENS = "max_tokens"
    TOOL_USE = "tool_use"
    STOP_SEQUENCE = "stop_sequence"


StopReasonType = Literal["end_turn", "max_tokens", "tool_use", "stop_sequence"]


def is_stop_reason_legal(stop_reason: str | None) -> bool:
    """
    Validate that a stop_reason value is known and expected.

    Returns:
        bool: True if the stop_reason is a known Anthropic value
    """
    if stop_reason is None:
        return False
    return stop_reason in {r.value for r in AnthropicStopReason}
