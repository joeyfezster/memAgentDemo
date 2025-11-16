from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Any, Literal, Optional

from letta_client.client import BaseTool
from pydantic import BaseModel, Field

from .repository import DATA_REPOSITORY


class TimeRange(BaseModel):
    start: date
    end: date


class GeoFilter(BaseModel):
    type: Literal["point_radius", "bounding_box", "polygon", "metro"]
    config: dict[str, Any]


class EntityReference(BaseModel):
    type: Literal["place", "chain"]
    id: str


class BenchmarkInput(BaseModel):
    type: Literal["category_region", "custom_set"]
    config: dict[str, Any]


class ClassificationThresholds(BaseModel):
    growing: float = Field(default=5.0)
    declining: float = Field(default=-5.0)


class PlacesSearchArgs(BaseModel):
    geo_filter: GeoFilter
    category_ids: Optional[list[str]] = None
    chain_ids: Optional[list[str]] = None
    text_query: Optional[str] = None
    portfolio_tags: Optional[list[str]] = None
    min_visits: Optional[int] = None
    limit: Optional[int] = Field(default=25)


class PlaceSummaryArgs(BaseModel):
    place_ids: list[str]
    time_range: TimeRange
    granularity: Literal["daily", "weekly", "monthly"] = "monthly"
    include_benchmark: bool = False
    include_rollup: bool = False


class PerformanceCompareArgs(BaseModel):
    entities: list[EntityReference]
    time_range: TimeRange
    metric: Literal["visits", "visit_frequency", "dwell_time"] = "visits"
    benchmark: Optional[BenchmarkInput] = None
    classification_thresholds: Optional[ClassificationThresholds] = None


class TradeAreaProfileArgs(BaseModel):
    place_ids: list[str]
    time_range: TimeRange
    output_geography: Literal["block_group", "census_tract", "zip", "cbg"] = "census_tract"
    include_demographics: bool = True
    include_psychographics: bool = False
    max_radius_km: Optional[float] = None


class AudienceProfileArgs(BaseModel):
    base_entities: list[EntityReference]
    comparison_entities: Optional[list[EntityReference]] = None
    baseline: Optional[dict[str, Any]] = None
    time_range: TimeRange
    dimensions: list[Literal["age", "income", "household_size", "kids", "lifestyle", "visit_frequency"]] = Field(
        default_factory=lambda: ["age", "income"]
    )


class VisitFlowsArgs(BaseModel):
    origin_place_ids: list[str]
    time_range: TimeRange
    window_before_minutes: int = 120
    window_after_minutes: int = 240
    group_by: Literal["destination_place", "destination_chain", "destination_category"] = "destination_place"
    min_shared_visitors: Optional[int] = None


def _time_range_dict(time_range: Optional[TimeRange]) -> Optional[dict[str, date]]:
    if not time_range:
        return None
    range_model = time_range if isinstance(time_range, TimeRange) else TimeRange.model_validate(time_range)
    return {"start": range_model.start, "end": range_model.end}


def _ensure_geo_filter(value: GeoFilter | dict[str, Any]) -> GeoFilter:
    return value if isinstance(value, GeoFilter) else GeoFilter.model_validate(value)


def _ensure_entity_reference(value: EntityReference | dict[str, Any]) -> EntityReference:
    return value if isinstance(value, EntityReference) else EntityReference.model_validate(value)


def _serialize_place(place: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": place["id"],
        "name": place["name"],
        "address": place["address"],
        "lat": place["lat"],
        "lon": place["lon"],
        "category_id": place["category_id"],
        "chain_id": place.get("chain_id"),
        "tags": place.get("tags", []),
        "annual_visits": place["annual_visits"],
    }


def _trend_payload(place: dict[str, Any]) -> dict[str, Any]:
    return {
        "yoy_change_pct": place.get("yoy_change_pct"),
        "mom_change_pct": place.get("mom_change_pct"),
        "classification": place.get("classification"),
    }


def _classification_label(value: float, thresholds: ClassificationThresholds) -> str:
    if value >= thresholds.growing:
        return "growing"
    if value <= thresholds.declining:
        return "declining"
    return "stable"


def _series_for_entity(entity: EntityReference, time_range: TimeRange, metric: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    time_dict = _time_range_dict(time_range)
    if entity.type == "place":
        place = DATA_REPOSITORY.get_place(entity.id)
        base_series = DATA_REPOSITORY.place_series(entity.id, time_dict)
        if metric == "visits":
            series = base_series
        else:
            value = place["visit_frequency"] if metric == "visit_frequency" else place["dwell_minutes"]
            series = [{"period": row["period"], "value": value} for row in base_series]
        return series, place
    chain = DATA_REPOSITORY.get_chain(entity.id)
    place_ids = chain.get("place_ids", [])
    periods: defaultdict[str, int] = defaultdict(int)
    for place_id in place_ids:
        for row in DATA_REPOSITORY.place_series(place_id, time_dict):
            periods[row["period"]] += row["visits"]
    sorted_periods = [
        {"period": key, "visits": value}
        for key, value in sorted(periods.items())
    ]
    if metric != "visits":
        aggregate_value = mean(
            DATA_REPOSITORY.get_place(pid)["visit_frequency"] if metric == "visit_frequency" else DATA_REPOSITORY.get_place(pid)["dwell_minutes"]
            for pid in place_ids
        ) if place_ids else 0
        sorted_periods = [{"period": row["period"], "value": aggregate_value} for row in sorted_periods]
    chain_payload = {
        "id": chain["id"],
        "name": chain["name"],
        "annual_visits": chain["annual_visits"],
        "yoy_change_pct": chain.get("yoy_change_pct", 0),
        "mom_change_pct": chain.get("mom_change_pct", 0),
        "visit_frequency": mean(
            DATA_REPOSITORY.get_place(pid)["visit_frequency"] for pid in place_ids
        ) if place_ids else 0,
        "dwell_minutes": mean(
            DATA_REPOSITORY.get_place(pid)["dwell_minutes"] for pid in place_ids
        ) if place_ids else 0,
        "classification": "growing" if chain.get("yoy_change_pct", 0) > 0 else "stable",
    }
    return sorted_periods, chain_payload


def _aggregate_series(series: list[dict[str, Any]]) -> float:
    if not series:
        return 0.0
    key = "visits" if "visits" in series[0] else "value"
    return sum(item[key] for item in series)


def _benchmark_value(entity_payload: dict[str, Any], benchmark: Optional[BenchmarkInput]) -> Optional[float]:
    if not benchmark:
        return None
    metric_value = entity_payload.get("annual_visits", 0)
    if benchmark.type == "category_region":
        category = benchmark.config.get("category_id")
        metro = benchmark.config.get("metro")
        peers = [
            place
            for place in DATA_REPOSITORY.places.values()
            if (not category or place["category_id"] == category)
            and (not metro or place["metro"] == metro)
        ]
        if not peers:
            return None
        average = mean(peer["annual_visits"] for peer in peers)
        if average == 0:
            return None
        return round((metric_value / average) * 100, 1)
    custom_ids = benchmark.config.get("entity_ids", [])
    if not custom_ids:
        return None
    values = []
    for entity_id in custom_ids:
        if entity_id in DATA_REPOSITORY.places:
            values.append(DATA_REPOSITORY.get_place(entity_id)["annual_visits"])
        elif entity_id in DATA_REPOSITORY.chains:
            values.append(DATA_REPOSITORY.get_chain(entity_id)["annual_visits"])
    if not values:
        return None
    baseline = mean(values)
    if baseline == 0:
        return None
    return round((metric_value / baseline) * 100, 1)


def _profile_dimensions(profile: dict[str, Any], dimensions: list[str]) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if "age" in dimensions:
        payload["age_distribution"] = profile.get("age_distribution")
    if "income" in dimensions:
        payload["income_distribution"] = profile.get("income_distribution")
    if "household_size" in dimensions:
        payload["household_size_distribution"] = profile.get("household_size_distribution")
    if "kids" in dimensions:
        payload["presence_of_kids_pct"] = profile.get("presence_of_kids_pct")
    if "lifestyle" in dimensions:
        payload["lifestyle_segments"] = profile.get("lifestyle_segments")
    if "visit_frequency" in dimensions:
        payload["visit_frequency_profile"] = profile.get("visit_frequency_profile")
    return payload


def _dimension_index(base: dict[str, float], baseline: dict[str, float]) -> dict[str, float]:
    index: dict[str, float] = {}
    for key, value in base.items():
        baseline_value = baseline.get(key) or 0.0001
        index[key] = round((value / baseline_value) * 100, 1)
    return index


def _similarity_score(profile_a: dict[str, Any], profile_b: dict[str, Any], dimensions: list[str]) -> float:
    sources = []
    if "age" in dimensions:
        sources.append((profile_a.get("age_distribution", {}), profile_b.get("age_distribution", {})))
    if "income" in dimensions:
        sources.append((profile_a.get("income_distribution", {}), profile_b.get("income_distribution", {})))
    if not sources:
        sources.append((profile_a.get("age_distribution", {}), profile_b.get("age_distribution", {})))
    distance = 0.0
    for left, right in sources:
        buckets = set(left.keys()) | set(right.keys())
        distance += sum(abs(left.get(bucket, 0) - right.get(bucket, 0)) for bucket in buckets)
    distance /= len(sources)
    score = max(0.0, 100.0 - distance * 200)
    return round(score, 1)


def _comparison_targets(entity: EntityReference) -> list[str]:
    if entity.type == "place":
        return [entity.id]
    chain = DATA_REPOSITORY.get_chain(entity.id)
    return chain.get("place_ids", [])


def _overlap_share(base: EntityReference, comparison: EntityReference) -> Optional[float]:
    base_targets = _comparison_targets(base)
    comparison_targets = _comparison_targets(comparison)
    for left in base_targets:
        for right in comparison_targets:
            share = DATA_REPOSITORY.overlap_share(left, right)
            if share is not None:
                return round(share, 2)
    return None


def _filter_flows_by_window(flow: dict[str, Any], before: int, after: int) -> bool:
    offset = flow.get("median_time_offset_minutes", 0)
    if offset < 0:
        return abs(offset) <= before
    return offset <= after


def _group_destination(flow: dict[str, Any], group_by: str) -> tuple[str, dict[str, Any]]:
    destination = flow["destination"]
    if group_by == "destination_place":
        return destination.get("id"), destination
    if group_by == "destination_chain":
        dest_id = destination.get("id")
        if destination.get("type") == "place" and dest_id in DATA_REPOSITORY.places:
            place = DATA_REPOSITORY.get_place(dest_id)
            chain_id = place.get("chain_id")
            if chain_id and chain_id in DATA_REPOSITORY.chains:
                chain = DATA_REPOSITORY.get_chain(chain_id)
                descriptor = {"type": "chain", "id": chain_id, "name": chain["name"]}
                return chain_id, descriptor
            descriptor = {"type": "place", "id": dest_id, "name": place["name"]}
            return dest_id, descriptor
        return dest_id, destination
    return destination.get("id"), destination


class PlacesSearchTool(BaseTool):
    name: str = "places.search_places"
    args_schema: type[BaseModel] = PlacesSearchArgs
    description: str = "Discover places given geography, category, and brand filters."

    def run(
        self,
        geo_filter: GeoFilter,
        category_ids: Optional[list[str]] = None,
        chain_ids: Optional[list[str]] = None,
        text_query: Optional[str] = None,
        portfolio_tags: Optional[list[str]] = None,
        min_visits: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> dict[str, Any]:
        geo_model = _ensure_geo_filter(geo_filter)
        places = DATA_REPOSITORY.search_places(
            geo_filter=geo_model.model_dump(),
            category_ids=category_ids,
            chain_ids=chain_ids,
            text_query=text_query,
            portfolio_tags=portfolio_tags,
            min_visits=min_visits,
            limit=limit,
        )
        return {"places": [_serialize_place(place) for place in places]}


class PlaceInsightsTool(BaseTool):
    name: str = "place_insights.get_place_summary"
    args_schema: type[BaseModel] = PlaceSummaryArgs
    description: str = "Summarize visit, dwell, and trend insights for places."

    def run(
        self,
        place_ids: list[str],
        time_range: TimeRange,
        granularity: str = "monthly",
        include_benchmark: bool = False,
        include_rollup: bool = False,
    ) -> dict[str, Any]:
        time_dict = _time_range_dict(time_range)
        summaries = []
        for place_id in place_ids:
            place = DATA_REPOSITORY.get_place(place_id)
            series = DATA_REPOSITORY.place_series(place_id, time_dict)
            total_visits = sum(row["visits"] for row in series)
            summary = {
                "place": _serialize_place(place),
                "visits": {"total": total_visits, "by_period": series, "granularity": granularity},
                "unique_visitors": place["unique_visitors"],
                "visit_frequency": place["visit_frequency"],
                "dwell_time": {"median_minutes": place["dwell_minutes"]},
                "trend": _trend_payload(place),
            }
            if include_benchmark:
                summary["benchmark"] = {"index": DATA_REPOSITORY.benchmark_index(place)}
            summaries.append(summary)
        payload: dict[str, Any] = {"places": summaries}
        if include_rollup:
            aggregate = DATA_REPOSITORY.aggregate_places(place_ids, time_dict)
            payload["rollup"] = aggregate
        return payload


class PerformanceCompareTool(BaseTool):
    name: str = "performance.compare_locations"
    args_schema: type[BaseModel] = PerformanceCompareArgs
    description: str = "Compare time-series performance across places or chains."

    def run(
        self,
        entities: list[EntityReference],
        time_range: TimeRange,
        metric: str = "visits",
        benchmark: Optional[BenchmarkInput] = None,
        classification_thresholds: Optional[ClassificationThresholds] = None,
    ) -> dict[str, Any]:
        thresholds = classification_thresholds or ClassificationThresholds()
        series_payload = []
        ranked_values = []
        normalized_entities = [_ensure_entity_reference(entity) for entity in entities]
        for entity in normalized_entities:
            series, entity_payload = _series_for_entity(entity, time_range, metric)
            total_value = _aggregate_series(series)
            ranked_values.append({"id": entity.id, "value": total_value})
            classification_value = entity_payload.get("yoy_change_pct", 0)
            series_payload.append(
                {
                    "entity": {"type": entity.type, "id": entity.id, "name": entity_payload.get("name", entity.id)},
                    "by_period": series,
                    "yoy_change_pct": entity_payload.get("yoy_change_pct"),
                    "mom_change_pct": entity_payload.get("mom_change_pct"),
                    "classification": _classification_label(classification_value, thresholds),
                    "benchmark_index": _benchmark_value(entity_payload, benchmark),
                }
            )
        ranked_values.sort(key=lambda item: item["value"], reverse=True)
        rankings = [{"metric": metric, "ranked_entities": [{"id": item["id"], "value": item["value"], "rank": idx + 1} for idx, item in enumerate(ranked_values)]}]
        return {"series": series_payload, "rankings": rankings}


class TradeAreaProfileTool(BaseTool):
    name: str = "trade_area.get_trade_area_profile"
    args_schema: type[BaseModel] = TradeAreaProfileArgs
    description: str = "Describe trade areas for places including geo-units and summaries."

    def run(
        self,
        place_ids: list[str],
        time_range: TimeRange,
        output_geography: str = "census_tract",
        include_demographics: bool = True,
        include_psychographics: bool = False,
        max_radius_km: Optional[float] = None,
    ) -> dict[str, Any]:
        profiles = []
        for place_id in place_ids:
            trade_area = DATA_REPOSITORY.get_trade_area(place_id)
            if not trade_area:
                continue
            geo_units = []
            for unit in trade_area["geo_units"]:
                if max_radius_km and unit.get("avg_distance_km") and unit["avg_distance_km"] > max_radius_km:
                    continue
                unit_payload = {key: value for key, value in unit.items() if key != "demographics"}
                if include_demographics and unit.get("demographics"):
                    unit_payload["demographics"] = unit["demographics"]
                if include_psychographics:
                    unit_payload["psychographics_index"] = 118
                geo_units.append(unit_payload)
            profiles.append(
                {
                    "place_id": place_id,
                    "trade_area_polygon": trade_area["trade_area_polygon"],
                    "geo_units": geo_units,
                    "summary": trade_area["summary"],
                    "output_geography": output_geography,
                }
            )
        return {"profiles": profiles}


class AudienceProfileTool(BaseTool):
    name: str = "audience.get_profile_and_overlap"
    args_schema: type[BaseModel] = AudienceProfileArgs
    description: str = "Describe visitor demographics and overlap for places or chains."

    def run(
        self,
        base_entities: list[EntityReference],
        time_range: TimeRange,
        comparison_entities: Optional[list[EntityReference]] = None,
        baseline: Optional[dict[str, Any]] = None,
        dimensions: Optional[list[str]] = None,
    ) -> dict[str, Any]:
        dimensions = dimensions or ["age", "income"]
        baseline_profile = DATA_REPOSITORY.baseline_profile(baseline)
        results = []
        normalized_bases = [_ensure_entity_reference(entity) for entity in base_entities]
        normalized_comparisons = (
            [_ensure_entity_reference(entity) for entity in comparison_entities]
            if comparison_entities
            else []
        )
        for entity in normalized_bases:
            profile = DATA_REPOSITORY.entity_profile(entity.type, entity.id)
            payload = {"entity": {"type": entity.type, "id": entity.id}, "profile": _profile_dimensions(profile, dimensions)}
            if baseline_profile:
                vs_baseline = {}
                if "age" in dimensions and profile.get("age_distribution") and baseline_profile.get("age_distribution"):
                    vs_baseline["age_index"] = _dimension_index(profile["age_distribution"], baseline_profile["age_distribution"])
                if "income" in dimensions and profile.get("income_distribution") and baseline_profile.get("income_distribution"):
                    vs_baseline["income_index"] = _dimension_index(profile["income_distribution"], baseline_profile["income_distribution"])
                payload["vs_baseline"] = vs_baseline
            overlaps = []
            for comparison in normalized_comparisons:
                comparison_profile = DATA_REPOSITORY.entity_profile(comparison.type, comparison.id)
                overlap = {
                    "comparison_entity": {"type": comparison.type, "id": comparison.id},
                    "audience_similarity_index": _similarity_score(profile, comparison_profile, dimensions),
                }
                share = _overlap_share(entity, comparison)
                if share is not None:
                    overlap["shared_visitor_pct"] = share
                overlaps.append(overlap)
            if overlaps:
                payload["overlaps"] = overlaps
            results.append(payload)
        return {"results": results}


class VisitFlowsTool(BaseTool):
    name: str = "journeys.get_visit_flows"
    args_schema: type[BaseModel] = VisitFlowsArgs
    description: str = "Reveal before and after visit flows for origin places."

    def run(
        self,
        origin_place_ids: list[str],
        time_range: TimeRange,
        window_before_minutes: int = 120,
        window_after_minutes: int = 240,
        group_by: str = "destination_place",
        min_shared_visitors: Optional[int] = None,
    ) -> dict[str, Any]:
        origins_payload = []
        aggregate: defaultdict[str, dict[str, Any]] = defaultdict(lambda: {"shared_visitors": 0, "visits": 0, "share_of_origin_visitors": 0.0, "samples": 0})
        for origin_id in origin_place_ids:
            flows = []
            for flow in DATA_REPOSITORY.flows_for_origin(origin_id):
                if not _filter_flows_by_window(flow, window_before_minutes, window_after_minutes):
                    continue
                if min_shared_visitors and flow.get("shared_visitors", 0) < min_shared_visitors:
                    continue
                key, destination = _group_destination(flow, group_by)
                flow_payload = {
                    "destination": destination,
                    "shared_visitors": flow.get("shared_visitors"),
                    "visits": flow.get("visits"),
                    "share_of_origin_visitors": flow.get("share_of_origin_visitors"),
                    "median_time_offset_minutes": flow.get("median_time_offset_minutes"),
                }
                flows.append(flow_payload)
                agg_entry = aggregate[key]
                agg_entry["destination"] = destination
                agg_entry["shared_visitors"] += flow.get("shared_visitors", 0)
                agg_entry["visits"] += flow.get("visits", 0)
                agg_entry["share_of_origin_visitors"] += flow.get("share_of_origin_visitors", 0.0)
                agg_entry["samples"] += 1
            origins_payload.append({"origin_place_id": origin_id, "flows_out": flows})
        aggregate_payload = []
        for entry in aggregate.values():
            avg_share = entry["share_of_origin_visitors"] / entry["samples"] if entry["samples"] else 0
            aggregate_payload.append(
                {
                    "destination": entry["destination"],
                    "shared_visitors": entry["shared_visitors"],
                    "visits": entry["visits"],
                    "share_of_origin_visitors": round(avg_share, 3),
                }
            )
        aggregate_payload.sort(key=lambda item: item["shared_visitors"], reverse=True)
        return {"origins": origins_payload, "aggregate": aggregate_payload}


def build_toolkit() -> list[BaseTool]:
    return [
        PlacesSearchTool(),
        PlaceInsightsTool(),
        PerformanceCompareTool(),
        TradeAreaProfileTool(),
        AudienceProfileTool(),
        VisitFlowsTool(),
    ]
