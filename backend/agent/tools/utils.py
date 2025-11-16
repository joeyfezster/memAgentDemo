from __future__ import annotations

import math
from datetime import date
from typing import Iterable

from . import datasets
from .schemas import TimeRange


def get_entity_metadata(entity_id: str) -> dict | None:
    if entity_id in datasets.PLACES:
        return datasets.PLACES[entity_id]
    if entity_id in datasets.CHAIN_DATA:
        return datasets.CHAIN_DATA[entity_id]
    return None


def ensure_time_range(value) -> TimeRange:
    if isinstance(value, TimeRange):
        return value
    return TimeRange(**value)


def filter_series(series: list[dict], time_range: TimeRange) -> list[dict]:
    filtered = []
    for entry in series:
        period = entry["period"]
        if time_range.start <= period <= time_range.end:
            filtered.append(entry)
    return filtered


def aggregate_series(series_list: list[list[dict]]) -> list[dict]:
    combined: dict[date, float] = {}
    for series in series_list:
        for entry in series:
            combined[entry["period"]] = combined.get(entry["period"], 0) + entry["value"]
    ordered = sorted(combined.items(), key=lambda item: item[0])
    return [{"period": period, "value": value} for period, value in ordered]


def get_metric_series(entity_id: str, metric: str) -> list[dict]:
    mapping = {
        "visits": datasets.VISIT_SERIES,
        "visit_frequency": datasets.VISIT_FREQUENCY_SERIES,
        "dwell_time": datasets.DWELL_TIME_SERIES,
    }
    if entity_id in mapping[metric]:
        return mapping[metric][entity_id]
    related = [place_id for place_id, place in datasets.PLACES.items() if place.get("chain_id") == entity_id]
    series_list = [mapping[metric][place_id] for place_id in related if place_id in mapping[metric]]
    if not series_list:
        return []
    return aggregate_series(series_list)


def period_growth(series: list[dict]) -> tuple[float, float]:
    if len(series) < 2:
        return 0.0, 0.0
    first = series[0]["value"]
    last = series[-1]["value"]
    yoy = ((last - first) / first) * 100 if first else 0.0
    prev = series[-2]["value"]
    mom = ((last - prev) / prev) * 100 if prev else 0.0
    return yoy, mom


def classify_trend(change: float, thresholds: dict | None) -> str:
    thresholds = thresholds or {"growing": 5.0, "declining": -5.0}
    if change >= thresholds["growing"]:
        return "growing"
    if change <= thresholds["declining"]:
        return "declining"
    return "stable"


def vector_similarity(a: dict[str, float], b: dict[str, float]) -> float:
    keys = set(a.keys()) | set(b.keys())
    distance = 0.0
    for key in keys:
        distance += abs(a.get(key, 0.0) - b.get(key, 0.0))
    score = max(0.0, 100.0 - distance * 100)
    return round(score, 2)


def audience_similarity(profile: dict, other: dict) -> float:
    age = vector_similarity(profile["age_distribution"], other["age_distribution"])
    income = vector_similarity(profile["income_distribution"], other["income_distribution"])
    household = vector_similarity(profile["household_size_distribution"], other["household_size_distribution"])
    kids = max(0.0, 100.0 - abs(profile["presence_of_kids_pct"] - other["presence_of_kids_pct"]) * 100)
    return round((age + income + household + kids) / 4, 2)


def resolve_baseline(baseline: dict | None) -> dict:
    if not baseline:
        return datasets.AUDIENCE_BASELINES["region_chicago"]
    baseline_id = baseline.get("id")
    return datasets.AUDIENCE_BASELINES.get(baseline_id, datasets.AUDIENCE_BASELINES["region_chicago"])


def shared_visitor_pct(base_id: str, comparison_id: str) -> float:
    value = datasets.VISITOR_OVERLAP.get((base_id, comparison_id))
    if value is None:
        value = datasets.VISITOR_OVERLAP.get((comparison_id, base_id), 0.15)
    return value


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return 6371 * c


def matches_geo_filter(place: dict, geo_filter) -> bool:
    if geo_filter is None:
        return True
    filter_type = geo_filter.type
    cfg = geo_filter.config or {}
    if filter_type == "metro":
        return place.get("metro") == cfg.get("id")
    if filter_type == "point_radius":
        center = cfg.get("center") or {}
        radius = cfg.get("radius_km", 10)
        distance = haversine_distance_km(place["lat"], place["lon"], center.get("lat"), center.get("lon"))
        return distance <= radius
    if filter_type == "bounding_box":
        bounds = cfg.get("bounds") or {}
        lat_min, lat_max = bounds.get("lat_min"), bounds.get("lat_max")
        lon_min, lon_max = bounds.get("lon_min"), bounds.get("lon_max")
        return lat_min <= place["lat"] <= lat_max and lon_min <= place["lon"] <= lon_max
    return True


def format_period_entries(series: Iterable[dict]) -> list[dict]:
    return [{"period": entry["period"].isoformat(), "value": entry["value"]} for entry in series]
