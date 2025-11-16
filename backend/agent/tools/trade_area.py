from __future__ import annotations

from letta_client.client import BaseTool

from . import datasets
from .schemas import TradeAreaInput
from .utils import ensure_time_range


class TradeAreaProfileTool(BaseTool):
    name: str = "trade_area.get_trade_area_profile"
    description: str = "Describe the geographies that contribute visitors to a place."
    args_schema: type[TradeAreaInput] = TradeAreaInput

    def run(
        self,
        place_ids: list[str],
        time_range: dict,
        output_geography: str = "zip",
        include_demographics: bool = True,
        include_psychographics: bool = True,
        max_radius_km: float | None = None,
    ) -> dict:
        ensure_time_range(time_range)
        results = []
        for place_id in place_ids:
            data = datasets.TRADE_AREA_DATA[place_id]
            geo_units = []
            for unit in data["geo_units"]:
                entry = {
                    "id": unit["id"],
                    "visits": unit["visits"],
                    "share_of_visits": unit["share_of_visits"],
                    "avg_distance_km": unit["avg_distance_km"],
                }
                if include_demographics:
                    entry["demographics"] = unit["demographics"]
                if include_psychographics:
                    entry["psychographics"] = unit["psychographics"]
                geo_units.append(entry)
            results.append(
                {
                    "place_id": place_id,
                    "trade_area_polygon": data["trade_area_polygon"],
                    "geo_units": geo_units,
                }
            )
        return {"status": "ok", "trade_areas": results}
