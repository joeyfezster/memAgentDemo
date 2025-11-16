from __future__ import annotations

from collections import defaultdict
from datetime import date
from statistics import mean
from typing import Any, Iterable, Optional

from .geo import bounds_from_points, haversine_km, within_bounds
from .mock_data import (
    MOCK_AUDIENCE_PROFILES,
    MOCK_BENCHMARKS,
    MOCK_CHAINS,
    MOCK_METROS,
    MOCK_PLACES,
    MOCK_TRADE_AREAS,
    MOCK_VISIT_FLOWS,
    MOCK_VISITOR_OVERLAP,
)


class MockDataRepository:
    def __init__(self) -> None:
        self.places = MOCK_PLACES
        self.chains = MOCK_CHAINS
        self.audience_profiles = MOCK_AUDIENCE_PROFILES
        self.benchmarks = MOCK_BENCHMARKS
        self.trade_areas = MOCK_TRADE_AREAS
        self.visit_flows = MOCK_VISIT_FLOWS
        self.visitor_overlap = MOCK_VISITOR_OVERLAP
        self.metros = MOCK_METROS

    def get_place(self, place_id: str) -> dict[str, Any]:
        return self.places[place_id]

    def get_chain(self, chain_id: str) -> dict[str, Any]:
        return self.chains[chain_id]

    def search_places(
        self,
        *,
        geo_filter: Optional[dict[str, Any]] = None,
        category_ids: Optional[list[str]] = None,
        chain_ids: Optional[list[str]] = None,
        text_query: Optional[str] = None,
        portfolio_tags: Optional[list[str]] = None,
        min_visits: Optional[int] = None,
        limit: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        results = list(self.places.values())
        if geo_filter:
            results = [place for place in results if self._match_geo(place, geo_filter)]
        if category_ids:
            allowed = set(category_ids)
            results = [place for place in results if place["category_id"] in allowed]
        if chain_ids:
            allowed = set(chain_ids)
            results = [place for place in results if place["chain_id"] in allowed]
        if text_query:
            text = text_query.lower()
            results = [place for place in results if text in place["name"].lower()]
        if portfolio_tags:
            tags = set(portfolio_tags)
            results = [place for place in results if tags.intersection(place.get("tags", []))]
        if min_visits:
            results = [place for place in results if place["annual_visits"] >= min_visits]
        results.sort(key=lambda item: item["annual_visits"], reverse=True)
        if limit:
            results = results[:limit]
        return results

    def _match_geo(self, place: dict[str, Any], geo_filter: dict[str, Any]) -> bool:
        filter_type = geo_filter.get("type")
        config = geo_filter.get("config", {}) or {}
        lat = place["lat"]
        lon = place["lon"]
        if filter_type == "point_radius":
            center_lat = config.get("lat", lat)
            center_lon = config.get("lon", lon)
            radius_km = config.get("radius_km", 5)
            return haversine_km(lat, lon, center_lat, center_lon) <= radius_km
        if filter_type == "bounding_box":
            return within_bounds(
                lat,
                lon,
                config.get("lat_min", lat - 0.1),
                config.get("lat_max", lat + 0.1),
                config.get("lon_min", lon - 0.1),
                config.get("lon_max", lon + 0.1),
            )
        if filter_type == "metro":
            bounds = self.metros.get(config.get("name") or config.get("id"))
            if not bounds:
                return True
            return within_bounds(lat, lon, bounds["lat_min"], bounds["lat_max"], bounds["lon_min"], bounds["lon_max"])
        if filter_type == "polygon":
            points = config.get("points") or []
            if not points:
                return True
            tuples = []
            for point in points:
                if isinstance(point, dict):
                    tuples.append((point.get("lat"), point.get("lon")))
                else:
                    tuples.append((point[0], point[1]))
            lat_min, lat_max, lon_min, lon_max = bounds_from_points(tuples)
            return within_bounds(lat, lon, lat_min, lat_max, lon_min, lon_max)
        return True

    def place_series(self, place_id: str, time_range: Optional[dict[str, date]] = None) -> list[dict[str, Any]]:
        place = self.get_place(place_id)
        return self._filter_periods(place["monthly_visits"], time_range)

    def _filter_periods(self, periods: Iterable[dict[str, Any]], time_range: Optional[dict[str, date]]) -> list[dict[str, Any]]:
        if not time_range:
            return list(periods)
        start = time_range.get("start")
        end = time_range.get("end")
        filtered = []
        for period in periods:
            period_date = date.fromisoformat(period["period"])
            if start and period_date < start:
                continue
            if end and period_date > end:
                continue
            filtered.append(period)
        return filtered

    def benchmark_index(self, place: dict[str, Any]) -> float:
        peers = [
            peer["annual_visits"]
            for peer in self.places.values()
            if peer["category_id"] == place["category_id"] and peer["metro"] == place["metro"]
        ]
        if not peers:
            return 100.0
        baseline = mean(peers)
        if baseline == 0:
            return 100.0
        return round((place["annual_visits"] / baseline) * 100, 1)

    def aggregate_places(self, place_ids: list[str], time_range: Optional[dict[str, date]]) -> dict[str, Any]:
        total_visits = 0
        periods: defaultdict[str, int] = defaultdict(int)
        yoy_values = []
        for place_id in place_ids:
            place = self.get_place(place_id)
            for period in self._filter_periods(place["monthly_visits"], time_range):
                periods[period["period"]] += period["visits"]
                total_visits += period["visits"]
            yoy_values.append(place["yoy_change_pct"])
        sorted_periods = [
            {"period": key, "visits": periods[key]}
            for key in sorted(periods.keys())
        ]
        avg_yoy = sum(yoy_values) / len(yoy_values) if yoy_values else 0
        return {"total_visits": total_visits, "by_period": sorted_periods, "avg_yoy": round(avg_yoy, 1)}

    def entity_profile(self, entity_type: str, entity_id: str) -> dict[str, Any]:
        if entity_type == "chain":
            base = {
                "age_distribution": {"18-24": 0.16, "25-34": 0.31, "35-44": 0.26, "45-54": 0.17, "55+": 0.1},
                "income_distribution": {"<50k": 0.28, "50-100k": 0.38, "100-150k": 0.22, "150k+": 0.12},
                "household_size_distribution": {"1": 0.24, "2": 0.32, "3": 0.24, "4+": 0.2},
                "presence_of_kids_pct": 0.4,
                "lifestyle_segments": [
                    {"name": "Baseline", "share_of_visitors": 1.0}
                ],
                "visit_frequency_profile": {"weekly": 0.25, "monthly": 0.5, "quarterly": 0.25},
            }
            return self.audience_profiles.get(entity_id, base)
        return self.audience_profiles.get(entity_id, self.audience_profiles["place_garden_state_plaza"])

    def baseline_profile(self, baseline: Optional[dict[str, Any]]) -> Optional[dict[str, Any]]:
        if not baseline:
            return None
        baseline_id = baseline.get("id")
        if not baseline_id:
            return None
        return self.benchmarks.get(baseline_id) or self.audience_profiles.get(baseline_id)

    def overlap_share(self, left_id: str, right_id: str) -> Optional[float]:
        direct = self.visitor_overlap.get((left_id, right_id))
        if direct is not None:
            return direct
        reverse = self.visitor_overlap.get((right_id, left_id))
        return reverse

    def get_trade_area(self, place_id: str) -> Optional[dict[str, Any]]:
        return self.trade_areas.get(place_id)

    def flows_for_origin(self, origin_id: str) -> list[dict[str, Any]]:
        return self.visit_flows.get(origin_id, [])


DATA_REPOSITORY = MockDataRepository()
