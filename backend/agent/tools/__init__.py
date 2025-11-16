from __future__ import annotations

from typing import Any

from .audience import AudienceProfileTool
from .journeys import JourneysVisitFlowsTool
from .performance import PerformanceCompareLocationsTool
from .place_insights import PlaceInsightsTool
from .places import PlacesSearchTool
from .trade_area import TradeAreaProfileTool


def get_all_tools() -> list:
    return [
        PlacesSearchTool(),
        PlaceInsightsTool(),
        AudienceProfileTool(),
        JourneysVisitFlowsTool(),
        PerformanceCompareLocationsTool(),
        TradeAreaProfileTool(),
    ]


__all__ = [
    "AudienceProfileTool",
    "JourneysVisitFlowsTool",
    "PerformanceCompareLocationsTool",
    "PlaceInsightsTool",
    "PlacesSearchTool",
    "TradeAreaProfileTool",
    "get_all_tools",
]


def register_tools_with_client(client: Any) -> list:
    created = []
    for tool in get_all_tools():
        created.append(client.tools.add(tool=tool))
    return created


__all__.append("register_tools_with_client")
