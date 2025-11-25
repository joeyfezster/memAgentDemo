import os
from datetime import UTC, datetime
from app.models.types import MemoryDocument

MODEL_NAME = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
MAX_TOKENS = int(os.getenv("ANTHROPIC_MAX_TOKENS", "4096"))
MAX_ITERATIONS = int(os.getenv("AGENT_MAX_ITERATIONS", "10"))
MAX_ITERATIONS_STREAMING = int(os.getenv("AGENT_MAX_ITERATIONS_STREAMING", "5"))

BASE_SYSTEM_PROMPT = """You are a helpful AI assistant for Placer Intelligence (Pi), a location analytics platform.

You help users understand location data, visitor patterns, and competitive insights for retail, real estate, and business intelligence purposes.

You have access to powerful tools that can search for places, analyze visitor data, and provide detailed analytics. When users ask about locations, businesses, or visitor patterns, USE THE AVAILABLE TOOLS to provide concrete data and insights. Don't just describe what the tools could do - actively use them to answer questions.

Be professional, concise, and data-focused in your responses.

IMPORTANT: Always follow user instructions precisely, including any specific formatting or response requirements they provide."""


def format_user_memory(memory: MemoryDocument) -> str:
    """Format user memory for inclusion in system prompt."""
    from app.models.types import PlacerPOI

    lines = ["USER'S STORED MEMORIES:"]

    active_facts = [f for f in memory.facts if f.is_active]
    if active_facts:
        for fact in active_facts:
            date_str = fact.added_at.split("T")[0]
            lines.append(f"- [{date_str}] {fact.content}")

    if memory.placer_user_datapoints:
        lines.append("\nPLACES OF INTEREST:")
        for poi in memory.placer_user_datapoints:
            if isinstance(poi, PlacerPOI):
                mention_count = sum(
                    len(mentions) for mentions in poi.mentioned_in.values()
                )
                poi_line = f"- {poi.place_name}"
                if poi.notes:
                    poi_line += f": {poi.notes}"
                poi_line += f" (mentioned in {mention_count} conversations)"
                lines.append(poi_line)

    return "\n".join(lines)


def build_system_prompt(user_display_name: str, user_memory: str | None = None) -> str:
    current_datetime = datetime.now(UTC).isoformat()
    prompt = f"""{BASE_SYSTEM_PROMPT}

Current datetime: {current_datetime}

The authenticated user's name in our system is {user_display_name}. However, if they prefer to be called by a different name, respect their preference and use the name they choose."""

    if user_memory:
        prompt += "\n\nThe following is relevant information you have previously stored about the user to help you provide better, more personalized responses:"
        prompt += f"\n\n{user_memory}"

    return prompt
