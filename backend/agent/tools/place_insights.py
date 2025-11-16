from __future__ import annotations

from letta_client.client import BaseTool

from . import datasets
from .schemas import PlaceSummaryInput
from .utils import (
    classify_trend,
    ensure_time_range,
    filter_series,
    format_period_entries,
    get_metric_series,
    period_growth,
)


class PlaceInsightsTool(BaseTool):
    name: str = "place_insights.get_place_summary"
    description: str = "Summarize visits, visitors, and trends for selected places."
    args_schema: type[PlaceSummaryInput] = PlaceSummaryInput

    def run(
        self,
        place_ids: list[str],
        time_range: dict,
        granularity: str = "monthly",
        include_benchmark: bool = True,
        include_rollup: bool = False,
    ) -> dict:
        requested_range = ensure_time_range(time_range)
        summaries = []
        for place_id in place_ids:
            place = datasets.PLACES[place_id]
            visit_series = filter_series(get_metric_series(place_id, "visits"), requested_range)
            total_visits = sum(entry["value"] for entry in visit_series)
            unique_visitors = datasets.PLACE_SUMMARY[place_id]["unique_visitors"]
            visit_frequency = round(total_visits / unique_visitors, 2)
            yoy, mom = period_growth(visit_series)
            benchmark_index = None
            if include_benchmark:
                baseline = datasets.BENCHMARK_BY_CATEGORY.get(place["category"], total_visits or 1)
                benchmark_index = round((total_visits / baseline) * 100, 1)
            summaries.append(
                {
                    "place": {
                        "id": place_id,
                        "name": place["name"],
                        "address": f"{place['address']}, {place['city']}, {place['state']}",
                        "lat": place["lat"],
                        "lon": place["lon"],
                        "category": place["category"],
                        "chain_id": place.get("chain_id"),
                    },
                    "visits": {
                        "total": total_visits,
                        "by_period": format_period_entries(visit_series),
                    },
                    "unique_visitors": unique_visitors,
                    "visit_frequency": visit_frequency,
                    "dwell_time": {
                        "median_minutes": datasets.PLACE_SUMMARY[place_id]["median_dwell"]
                    },
                    "trend": {
                        "yoy_change_pct": round(yoy, 2),
                        "mom_change_pct": round(mom, 2),
                        "classification": classify_trend(yoy, None),
                    },
                    "benchmark": {
                        "index": benchmark_index,
                        "baseline_category_average": datasets.BENCHMARK_BY_CATEGORY.get(place["category"]),
                    }
                    if include_benchmark
                    else None,
                }
            )
        result = {"status": "ok", "places": summaries}
        if include_rollup:
            total_visits = sum(place["visits"]["total"] for place in summaries)
            total_unique = sum(place["unique_visitors"] for place in summaries)
            rollup_frequency = round(total_visits / total_unique, 2) if total_unique else 0
            result["rollup"] = {
                "visits": total_visits,
                "unique_visitors": total_unique,
                "visit_frequency": rollup_frequency,
            }
        return result
