from __future__ import annotations

from letta_client.client import BaseTool

from . import datasets
from .schemas import JourneyInput
from .utils import ensure_time_range


def group_flows(flows: list[dict], group_by: str) -> list[dict]:
    if group_by == "destination_place":
        return flows
    aggregated: dict[str, dict] = {}
    for flow in flows:
        destination_id = flow["destination"]["id"]
        metadata = datasets.PLACES[destination_id]
        if group_by == "destination_chain" and metadata.get("chain_id"):
            key = metadata["chain_id"]
            name = metadata["chain_name"]
            destination = {"type": "chain", "id": key, "name": name}
        elif group_by == "destination_category":
            key = metadata["category"]
            destination = {"type": "category", "id": key, "name": key.replace("_", " ").title()}
        else:
            key = destination_id
            destination = flow["destination"]
        current = aggregated.setdefault(
            key,
            {
                "destination": destination,
                "shared_visitors": 0,
                "visits": 0,
                "share_of_origin_visitors": 0.0,
                "median_time_offset_minutes": flow["median_time_offset_minutes"],
            },
        )
        current["shared_visitors"] += flow["shared_visitors"]
        current["visits"] += flow["visits"]
        current["share_of_origin_visitors"] += flow["share_of_origin_visitors"]
    return list(aggregated.values())


class JourneysVisitFlowsTool(BaseTool):
    name: str = "journeys.get_visit_flows"
    description: str = "Reveal where visitors go before and after a selected origin place."
    args_schema: type[JourneyInput] = JourneyInput

    def run(
        self,
        origin_place_ids: list[str],
        time_range: dict,
        window_before_minutes: int = 120,
        window_after_minutes: int = 240,
        group_by: str = "destination_place",
        min_shared_visitors: int = 0,
    ) -> dict:
        ensure_time_range(time_range)
        results = []
        for origin_id in origin_place_ids:
            flows = datasets.JOURNEY_FLOWS.get(origin_id, [])
            filtered = [flow for flow in flows if flow["shared_visitors"] >= min_shared_visitors]
            grouped = group_flows(filtered, group_by)
            results.append({"origin_place_id": origin_id, "flows_out": grouped})
        return {"status": "ok", "results": results}
