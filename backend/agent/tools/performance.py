from __future__ import annotations

from letta_client.client import BaseTool

from . import datasets
from .schemas import PerformanceInput
from .utils import (
    classify_trend,
    ensure_time_range,
    filter_series,
    format_period_entries,
    get_entity_metadata,
    get_metric_series,
    period_growth,
)


class PerformanceCompareLocationsTool(BaseTool):
    name: str = "performance.compare_locations"
    description: str = "Compare performance trends for multiple places or chains."
    args_schema: type[PerformanceInput] = PerformanceInput

    def run(
        self,
        entities: list[dict],
        time_range: dict,
        metric: str = "visits",
        benchmark: dict | None = None,
        classification_thresholds: dict | None = None,
    ) -> dict:
        requested_range = ensure_time_range(time_range)
        series_payload = []
        ranking_values = []
        for entity in entities:
            entity_id = entity["id"]
            series = filter_series(get_metric_series(entity_id, metric), requested_range)
            total_value = sum(entry["value"] for entry in series)
            yoy, mom = period_growth(series)
            metadata = get_entity_metadata(entity_id)
            benchmark_index = None
            if benchmark and metadata and metadata.get("category") in datasets.BENCHMARK_BY_CATEGORY:
                baseline_value = datasets.BENCHMARK_BY_CATEGORY[metadata["category"]]
                benchmark_index = round((total_value / baseline_value) * 100, 1)
            series_payload.append(
                {
                    "entity": entity,
                    "by_period": format_period_entries(series),
                    "yoy_change_pct": round(yoy, 2),
                    "mom_change_pct": round(mom, 2),
                    "classification": classify_trend(yoy, classification_thresholds),
                    "benchmark_index": benchmark_index,
                    "total": total_value,
                }
            )
            ranking_values.append((entity, total_value))
        ranking_values.sort(key=lambda item: item[1], reverse=True)
        rankings = [
            {"entity": item[0], "value": item[1], "rank": idx + 1}
            for idx, item in enumerate(ranking_values)
        ]
        return {"status": "ok", "series": series_payload, "rankings": rankings}
