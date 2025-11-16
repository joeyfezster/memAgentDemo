from __future__ import annotations

from letta_client.client import BaseTool

from . import datasets
from .schemas import GeoFilter, SearchPlacesInput
from .utils import matches_geo_filter


class PlacesSearchTool(BaseTool):
    name: str = "places.search_places"
    description: str = "Discover places that match geography, category, chain, and text filters."
    args_schema: type[SearchPlacesInput] = SearchPlacesInput

    def run(
        self,
        geo_filter: dict | None = None,
        category_ids: list[str] | None = None,
        chain_ids: list[str] | None = None,
        text_query: str | None = None,
        portfolio_tags: list[str] | None = None,
        min_visits: int | None = None,
        limit: int = 10,
    ) -> dict:
        parsed_filter = GeoFilter(**geo_filter) if geo_filter else None
        lower_query = text_query.lower() if text_query else None
        category_set = set(category_ids or [])
        chain_set = set(chain_ids or [])
        tag_set = set(portfolio_tags or [])
        places = []
        for place in datasets.PLACES.values():
            if not matches_geo_filter(place, parsed_filter):
                continue
            if category_set and place["category"] not in category_set:
                continue
            if chain_set and place.get("chain_id") not in chain_set:
                continue
            if lower_query and lower_query not in place["name"].lower():
                continue
            if tag_set and not tag_set.intersection(place["portfolio_tags"]):
                continue
            if min_visits and place["visits_last_12m"] < min_visits:
                continue
            places.append(
                {
                    "id": place["id"],
                    "name": place["name"],
                    "address": f"{place['address']}, {place['city']}, {place['state']}",
                    "lat": place["lat"],
                    "lon": place["lon"],
                    "category": place["category"],
                    "chain_id": place["chain_id"],
                    "chain_name": place["chain_name"],
                    "portfolio_tags": place["portfolio_tags"],
                    "visits_last_12m": place["visits_last_12m"],
                }
            )
        places.sort(key=lambda item: item["visits_last_12m"], reverse=True)
        return {"status": "ok", "places": places[:limit]}
