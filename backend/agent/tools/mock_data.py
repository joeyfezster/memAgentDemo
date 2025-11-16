from __future__ import annotations

from datetime import date
from typing import Any


MOCK_METROS: dict[str, dict[str, float]] = {
    "nyc": {"lat_min": 40.4, "lat_max": 41.4, "lon_min": -74.5, "lon_max": -73.0},
    "atlanta": {"lat_min": 33.4, "lat_max": 34.2, "lon_min": -84.8, "lon_max": -84.0},
}


def _monthly(values: list[int]) -> list[dict[str, Any]]:
    periods = []
    for idx, visits in enumerate(values, start=1):
        periods.append({"period": date(2024, idx, 1).isoformat(), "visits": visits})
    return periods


MOCK_PLACES: dict[str, dict[str, Any]] = {
    "place_garden_state_plaza": {
        "id": "place_garden_state_plaza",
        "name": "Garden State Plaza",
        "address": "1 Garden State Plaza, Paramus, NJ",
        "lat": 40.918,
        "lon": -74.076,
        "category_id": "regional_mall",
        "chain_id": None,
        "tags": ["our_centers"],
        "metro": "nyc",
        "annual_visits": 12100000,
        "monthly_visits": _monthly([910000, 890000, 930000, 950000, 990000, 1010000, 1030000, 1045000, 1000000, 980000, 960000, 940000]),
        "unique_visitors": 2550000,
        "visit_frequency": 4.7,
        "dwell_minutes": 96,
        "yoy_change_pct": 6.3,
        "mom_change_pct": 1.1,
        "classification": "growing",
    },
    "place_willowbrook_center": {
        "id": "place_willowbrook_center",
        "name": "Willowbrook Center",
        "address": "25 Willowbrook Blvd, Wayne, NJ",
        "lat": 40.889,
        "lon": -74.258,
        "category_id": "regional_mall",
        "chain_id": None,
        "tags": ["our_centers"],
        "metro": "nyc",
        "annual_visits": 8700000,
        "monthly_visits": _monthly([720000, 700000, 730000, 750000, 780000, 820000, 850000, 860000, 820000, 790000, 760000, 750000]),
        "unique_visitors": 1820000,
        "visit_frequency": 4.1,
        "dwell_minutes": 82,
        "yoy_change_pct": 2.4,
        "mom_change_pct": 0.8,
        "classification": "stable",
    },
    "place_paramus_drive_chickfila": {
        "id": "place_paramus_drive_chickfila",
        "name": "Chick-fil-A Paramus Drive",
        "address": "400 NJ-17, Paramus, NJ",
        "lat": 40.9603,
        "lon": -74.074,
        "category_id": "fast_casual",
        "chain_id": "chain_chickfila",
        "tags": ["rmn_flagship"],
        "metro": "nyc",
        "annual_visits": 1600000,
        "monthly_visits": _monthly([120000, 115000, 130000, 135000, 140000, 150000, 155000, 158000, 150000, 145000, 140000, 138000]),
        "unique_visitors": 420000,
        "visit_frequency": 3.8,
        "dwell_minutes": 34,
        "yoy_change_pct": 9.8,
        "mom_change_pct": 1.6,
        "classification": "growing",
    },
    "place_paramus_quickstop": {
        "id": "place_paramus_quickstop",
        "name": "QuickStop Paramus",
        "address": "45 Ridgewood Ave, Paramus, NJ",
        "lat": 40.9531,
        "lon": -74.0705,
        "category_id": "convenience",
        "chain_id": "chain_quickstop",
        "tags": ["priority_outlet"],
        "metro": "nyc",
        "annual_visits": 980000,
        "monthly_visits": _monthly([76000, 72000, 78000, 80000, 83000, 85000, 87000, 90000, 86000, 82000, 79000, 78000]),
        "unique_visitors": 210000,
        "visit_frequency": 4.2,
        "dwell_minutes": 12,
        "yoy_change_pct": 4.1,
        "mom_change_pct": 1.0,
        "classification": "growing",
    },
    "place_eagle_creek_golf": {
        "id": "place_eagle_creek_golf",
        "name": "Eagle Creek Golf Club",
        "address": "8000 Eagle Creek Pkwy, Atlanta, GA",
        "lat": 33.645,
        "lon": -84.465,
        "category_id": "golf_course",
        "chain_id": "chain_greenfairways",
        "tags": ["golf_focus"],
        "metro": "atlanta",
        "annual_visits": 540000,
        "monthly_visits": _monthly([36000, 34000, 38000, 42000, 46000, 52000, 58000, 60000, 55000, 50000, 44000, 39000]),
        "unique_visitors": 132000,
        "visit_frequency": 3.2,
        "dwell_minutes": 148,
        "yoy_change_pct": 7.5,
        "mom_change_pct": 2.2,
        "classification": "growing",
    },
    "place_green_valley_golf": {
        "id": "place_green_valley_golf",
        "name": "Green Valley Links",
        "address": "1900 Green Valley Rd, Atlanta, GA",
        "lat": 33.712,
        "lon": -84.39,
        "category_id": "golf_course",
        "chain_id": "chain_greenfairways",
        "tags": ["golf_focus"],
        "metro": "atlanta",
        "annual_visits": 480000,
        "monthly_visits": _monthly([32000, 30000, 34000, 36000, 40000, 45000, 52000, 54000, 50000, 46000, 41000, 37000]),
        "unique_visitors": 118000,
        "visit_frequency": 3.0,
        "dwell_minutes": 142,
        "yoy_change_pct": 5.9,
        "mom_change_pct": 1.7,
        "classification": "growing",
    },
    "place_midtown_quickstop": {
        "id": "place_midtown_quickstop",
        "name": "QuickStop Midtown",
        "address": "1550 Peachtree St NE, Atlanta, GA",
        "lat": 33.793,
        "lon": -84.387,
        "category_id": "convenience",
        "chain_id": "chain_quickstop",
        "tags": ["priority_outlet"],
        "metro": "atlanta",
        "annual_visits": 760000,
        "monthly_visits": _monthly([61000, 59000, 64000, 66000, 70000, 72000, 75000, 78000, 72000, 68000, 64000, 62000]),
        "unique_visitors": 182000,
        "visit_frequency": 3.9,
        "dwell_minutes": 11,
        "yoy_change_pct": 3.4,
        "mom_change_pct": 0.9,
        "classification": "stable",
    },
    "place_peachtree_bar": {
        "id": "place_peachtree_bar",
        "name": "Peachtree Fairway Bar",
        "address": "930 Peachtree St NE, Atlanta, GA",
        "lat": 33.7805,
        "lon": -84.3888,
        "category_id": "bar",
        "chain_id": None,
        "tags": ["partner_brand"],
        "metro": "atlanta",
        "annual_visits": 410000,
        "monthly_visits": _monthly([29000, 28000, 31000, 33000, 35000, 36000, 38000, 39000, 36000, 34000, 32000, 30000]),
        "unique_visitors": 110000,
        "visit_frequency": 3.5,
        "dwell_minutes": 88,
        "yoy_change_pct": 4.8,
        "mom_change_pct": 1.2,
        "classification": "stable",
    },
}


MOCK_CHAINS: dict[str, dict[str, Any]] = {
    "chain_chickfila": {
        "id": "chain_chickfila",
        "name": "Chick-fil-A",
        "category_id": "fast_casual",
        "place_ids": ["place_paramus_drive_chickfila"],
        "annual_visits": 1600000,
        "yoy_change_pct": 9.8,
    },
    "chain_quickstop": {
        "id": "chain_quickstop",
        "name": "QuickStop",
        "category_id": "convenience",
        "place_ids": ["place_paramus_quickstop", "place_midtown_quickstop"],
        "annual_visits": 1740000,
        "yoy_change_pct": 3.8,
    },
    "chain_greenfairways": {
        "id": "chain_greenfairways",
        "name": "Green Fairways Golf",
        "category_id": "golf_course",
        "place_ids": ["place_eagle_creek_golf", "place_green_valley_golf"],
        "annual_visits": 1020000,
        "yoy_change_pct": 6.7,
    },
}


MOCK_AUDIENCE_PROFILES: dict[str, dict[str, Any]] = {
    "place_garden_state_plaza": {
        "age_distribution": {"18-24": 0.12, "25-34": 0.26, "35-44": 0.24, "45-54": 0.18, "55+": 0.2},
        "income_distribution": {"<50k": 0.22, "50-100k": 0.38, "100-150k": 0.26, "150k+": 0.14},
        "household_size_distribution": {"1": 0.28, "2": 0.32, "3": 0.22, "4+": 0.18},
        "presence_of_kids_pct": 0.41,
        "lifestyle_segments": [
            {"name": "Fashion Families", "share_of_visitors": 0.33},
            {"name": "Experiential Seekers", "share_of_visitors": 0.21},
        ],
        "visit_frequency_profile": {"weekly": 0.19, "monthly": 0.52, "quarterly": 0.29},
    },
    "place_willowbrook_center": {
        "age_distribution": {"18-24": 0.10, "25-34": 0.24, "35-44": 0.26, "45-54": 0.21, "55+": 0.19},
        "income_distribution": {"<50k": 0.26, "50-100k": 0.36, "100-150k": 0.24, "150k+": 0.14},
        "household_size_distribution": {"1": 0.26, "2": 0.34, "3": 0.22, "4+": 0.18},
        "presence_of_kids_pct": 0.39,
        "lifestyle_segments": [
            {"name": "Value Suburbanites", "share_of_visitors": 0.37},
            {"name": "Social Families", "share_of_visitors": 0.19},
        ],
        "visit_frequency_profile": {"weekly": 0.16, "monthly": 0.49, "quarterly": 0.35},
    },
    "place_paramus_drive_chickfila": {
        "age_distribution": {"18-24": 0.18, "25-34": 0.33, "35-44": 0.24, "45-54": 0.16, "55+": 0.09},
        "income_distribution": {"<50k": 0.32, "50-100k": 0.34, "100-150k": 0.22, "150k+": 0.12},
        "household_size_distribution": {"1": 0.22, "2": 0.29, "3": 0.26, "4+": 0.23},
        "presence_of_kids_pct": 0.47,
        "lifestyle_segments": [
            {"name": "Busy Families", "share_of_visitors": 0.42},
            {"name": "Digital Nomads", "share_of_visitors": 0.17},
        ],
        "visit_frequency_profile": {"weekly": 0.31, "monthly": 0.48, "quarterly": 0.21},
    },
    "place_eagle_creek_golf": {
        "age_distribution": {"18-24": 0.06, "25-34": 0.18, "35-44": 0.29, "45-54": 0.27, "55+": 0.2},
        "income_distribution": {"<50k": 0.08, "50-100k": 0.22, "100-150k": 0.34, "150k+": 0.36},
        "household_size_distribution": {"1": 0.18, "2": 0.36, "3": 0.24, "4+": 0.22},
        "presence_of_kids_pct": 0.28,
        "lifestyle_segments": [
            {"name": "Affluent Athletes", "share_of_visitors": 0.44},
            {"name": "Upscale Empty Nesters", "share_of_visitors": 0.26},
        ],
        "visit_frequency_profile": {"weekly": 0.24, "monthly": 0.53, "quarterly": 0.23},
    },
    "place_green_valley_golf": {
        "age_distribution": {"18-24": 0.07, "25-34": 0.2, "35-44": 0.28, "45-54": 0.25, "55+": 0.2},
        "income_distribution": {"<50k": 0.1, "50-100k": 0.26, "100-150k": 0.32, "150k+": 0.32},
        "household_size_distribution": {"1": 0.2, "2": 0.34, "3": 0.24, "4+": 0.22},
        "presence_of_kids_pct": 0.31,
        "lifestyle_segments": [
            {"name": "Active Upscalers", "share_of_visitors": 0.41},
            {"name": "Weekend Warriors", "share_of_visitors": 0.24},
        ],
        "visit_frequency_profile": {"weekly": 0.22, "monthly": 0.51, "quarterly": 0.27},
    },
    "chain_quickstop": {
        "age_distribution": {"18-24": 0.16, "25-34": 0.32, "35-44": 0.26, "45-54": 0.16, "55+": 0.1},
        "income_distribution": {"<50k": 0.34, "50-100k": 0.4, "100-150k": 0.18, "150k+": 0.08},
        "household_size_distribution": {"1": 0.24, "2": 0.31, "3": 0.25, "4+": 0.2},
        "presence_of_kids_pct": 0.43,
        "lifestyle_segments": [
            {"name": "Everyday Errands", "share_of_visitors": 0.48},
            {"name": "Young Strivers", "share_of_visitors": 0.22},
        ],
        "visit_frequency_profile": {"weekly": 0.37, "monthly": 0.44, "quarterly": 0.19},
    },
}


MOCK_BENCHMARKS: dict[str, dict[str, Any]] = {
    "regional_mall_nyc": {
        "age_distribution": {"18-24": 0.11, "25-34": 0.25, "35-44": 0.25, "45-54": 0.2, "55+": 0.19},
        "income_distribution": {"<50k": 0.24, "50-100k": 0.37, "100-150k": 0.25, "150k+": 0.14},
    },
    "atlanta_metro": {
        "age_distribution": {"18-24": 0.14, "25-34": 0.28, "35-44": 0.23, "45-54": 0.17, "55+": 0.18},
        "income_distribution": {"<50k": 0.31, "50-100k": 0.4, "100-150k": 0.2, "150k+": 0.09},
    },
}


MOCK_TRADE_AREAS: dict[str, dict[str, Any]] = {
    "place_garden_state_plaza": {
        "trade_area_polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-74.1, 40.9],
                    [-74.02, 40.9],
                    [-74.02, 41.0],
                    [-74.1, 41.0],
                    [-74.1, 40.9],
                ]
            ],
        },
        "geo_units": [
            {"id": "0701", "visits": 1200000, "share_of_visits": 0.32, "avg_distance_km": 8.1},
            {"id": "0702", "visits": 900000, "share_of_visits": 0.24, "avg_distance_km": 12.4},
            {"id": "0703", "visits": 640000, "share_of_visits": 0.17, "avg_distance_km": 18.3},
        ],
        "summary": {
            "median_distance_km": 14.2,
            "top_n_geo_units": ["0701", "0702", "0703"],
            "diversity_index": 0.78,
        },
    },
    "place_paramus_drive_chickfila": {
        "trade_area_polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-74.09, 40.95],
                    [-74.03, 40.95],
                    [-74.03, 40.99],
                    [-74.09, 40.99],
                    [-74.09, 40.95],
                ]
            ],
        },
        "geo_units": [
            {"id": "0701", "visits": 210000, "share_of_visits": 0.32, "avg_distance_km": 5.4},
            {"id": "0704", "visits": 150000, "share_of_visits": 0.23, "avg_distance_km": 7.2},
            {"id": "0705", "visits": 118000, "share_of_visits": 0.18, "avg_distance_km": 11.8},
        ],
        "summary": {
            "median_distance_km": 8.7,
            "top_n_geo_units": ["0701", "0704", "0705"],
            "diversity_index": 0.69,
        },
    },
    "place_eagle_creek_golf": {
        "trade_area_polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-84.5, 33.61],
                    [-84.39, 33.61],
                    [-84.39, 33.69],
                    [-84.5, 33.69],
                    [-84.5, 33.61],
                ]
            ],
        },
        "geo_units": [
            {"id": "13121", "visits": 76000, "share_of_visits": 0.28, "avg_distance_km": 16.2, "demographics": {"median_income": 120000}},
            {"id": "13135", "visits": 62000, "share_of_visits": 0.23, "avg_distance_km": 20.5, "demographics": {"median_income": 98000}},
            {"id": "13139", "visits": 54000, "share_of_visits": 0.2, "avg_distance_km": 28.6, "demographics": {"median_income": 87000}},
        ],
        "summary": {
            "median_distance_km": 21.3,
            "top_n_geo_units": ["13121", "13135", "13139"],
            "diversity_index": 0.72,
        },
    },
}


MOCK_VISITOR_OVERLAP: dict[tuple[str, str], float] = {
    ("place_eagle_creek_golf", "place_midtown_quickstop"): 0.37,
    ("place_eagle_creek_golf", "place_peachtree_bar"): 0.29,
    ("place_green_valley_golf", "place_midtown_quickstop"): 0.33,
    ("place_green_valley_golf", "place_peachtree_bar"): 0.31,
    ("place_paramus_drive_chickfila", "place_paramus_quickstop"): 0.42,
}


MOCK_VISIT_FLOWS: dict[str, list[dict[str, Any]]] = {
    "place_eagle_creek_golf": [
        {
            "destination": {"type": "place", "id": "place_midtown_quickstop", "name": "QuickStop Midtown"},
            "shared_visitors": 12000,
            "visits": 16000,
            "share_of_origin_visitors": 0.23,
            "median_time_offset_minutes": 65,
        },
        {
            "destination": {"type": "place", "id": "place_peachtree_bar", "name": "Peachtree Fairway Bar"},
            "shared_visitors": 9800,
            "visits": 15000,
            "share_of_origin_visitors": 0.19,
            "median_time_offset_minutes": 145,
        },
        {
            "destination": {"type": "category", "id": "grocery", "name": "Grocery Stores"},
            "shared_visitors": 8600,
            "visits": 12000,
            "share_of_origin_visitors": 0.16,
            "median_time_offset_minutes": -40,
        },
    ],
    "place_green_valley_golf": [
        {
            "destination": {"type": "place", "id": "place_midtown_quickstop", "name": "QuickStop Midtown"},
            "shared_visitors": 10500,
            "visits": 14000,
            "share_of_origin_visitors": 0.22,
            "median_time_offset_minutes": 55,
        },
        {
            "destination": {"type": "category", "id": "bar", "name": "Bars"},
            "shared_visitors": 9100,
            "visits": 13000,
            "share_of_origin_visitors": 0.19,
            "median_time_offset_minutes": 130,
        },
        {
            "destination": {"type": "chain", "id": "chain_quickstop", "name": "QuickStop"},
            "shared_visitors": 8700,
            "visits": 12500,
            "share_of_origin_visitors": 0.18,
            "median_time_offset_minutes": 70,
        },
    ],
}
