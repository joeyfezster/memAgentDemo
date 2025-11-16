from __future__ import annotations

from math import atan2, cos, radians, sin, sqrt
from typing import Iterable, Tuple


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    radius = 6371.0
    d_lat = radians(lat2 - lat1)
    d_lon = radians(lon2 - lon1)
    a = sin(d_lat / 2) ** 2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(d_lon / 2) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    return radius * c


def bounds_from_points(points: Iterable[Tuple[float, float]]) -> tuple[float, float, float, float]:
    lats, lons = zip(*points)
    return min(lats), max(lats), min(lons), max(lons)


def within_bounds(lat: float, lon: float, lat_min: float, lat_max: float, lon_min: float, lon_max: float) -> bool:
    return lat_min <= lat <= lat_max and lon_min <= lon <= lon_max
