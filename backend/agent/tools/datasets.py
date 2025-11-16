from __future__ import annotations

from datetime import date

PLACES = {
    "plc_northwood_town_center": {
        "id": "plc_northwood_town_center",
        "name": "Northwood Town Center",
        "address": "1200 Market St",
        "city": "Northwood",
        "state": "IL",
        "lat": 41.915,
        "lon": -87.71,
        "category": "regional_mall",
        "chain_id": None,
        "chain_name": None,
        "metro": "chicago",
        "portfolio_tags": ["priority_centers", "owned"],
        "visits_last_12m": 1820000,
    },
    "plc_summit_ridge_golf": {
        "id": "plc_summit_ridge_golf",
        "name": "Summit Ridge Golf Club",
        "address": "2550 Fairway Ln",
        "city": "Oak Ridge",
        "state": "IL",
        "lat": 41.882,
        "lon": -88.02,
        "category": "golf_course",
        "chain_id": None,
        "chain_name": None,
        "metro": "chicago",
        "portfolio_tags": ["golf_focus"],
        "visits_last_12m": 320000,
    },
    "plc_riverbend_plaza": {
        "id": "plc_riverbend_plaza",
        "name": "Riverbend Plaza",
        "address": "845 Riverside Dr",
        "city": "Riverbend",
        "state": "IL",
        "lat": 41.78,
        "lon": -87.93,
        "category": "neighborhood_center",
        "chain_id": None,
        "chain_name": None,
        "metro": "chicago",
        "portfolio_tags": ["owned"],
        "visits_last_12m": 640000,
    },
    "plc_quickmart_lakeview": {
        "id": "plc_quickmart_lakeview",
        "name": "QuickMart Lakeview",
        "address": "4112 N Sheridan Rd",
        "city": "Chicago",
        "state": "IL",
        "lat": 41.957,
        "lon": -87.654,
        "category": "convenience",
        "chain_id": "chn_quickmart",
        "chain_name": "QuickMart Express",
        "metro": "chicago",
        "portfolio_tags": ["priority_convenience"],
        "visits_last_12m": 280000,
    },
    "plc_freshmart_aurora": {
        "id": "plc_freshmart_aurora",
        "name": "FreshMart Aurora",
        "address": "1802 Fox Valley Ctr",
        "city": "Aurora",
        "state": "IL",
        "lat": 41.76,
        "lon": -88.21,
        "category": "grocery",
        "chain_id": "chn_freshmart",
        "chain_name": "FreshMart",
        "metro": "chicago",
        "portfolio_tags": ["priority_centers"],
        "visits_last_12m": 720000,
    },
    "plc_lakeview_taphouse": {
        "id": "plc_lakeview_taphouse",
        "name": "Lakeview Taphouse",
        "address": "3200 N Clark St",
        "city": "Chicago",
        "state": "IL",
        "lat": 41.94,
        "lon": -87.65,
        "category": "bar",
        "chain_id": None,
        "chain_name": None,
        "metro": "chicago",
        "portfolio_tags": ["partner"],
        "visits_last_12m": 210000,
    },
}

CHAIN_DATA = {
    "chn_quickmart": {
        "id": "chn_quickmart",
        "name": "QuickMart Express",
        "category": "convenience",
    },
    "chn_freshmart": {
        "id": "chn_freshmart",
        "name": "FreshMart",
        "category": "grocery",
    },
}

ENTITY_NAMES = {entity["id"]: entity["name"] for entity in PLACES.values()}
ENTITY_NAMES.update({entity["id"]: entity["name"] for entity in CHAIN_DATA.values()})

BENCHMARK_BY_CATEGORY = {
    "regional_mall": 1500000,
    "golf_course": 280000,
    "neighborhood_center": 520000,
    "convenience": 240000,
    "grocery": 600000,
    "bar": 180000,
}

VISIT_SERIES = {
    "plc_northwood_town_center": [
        {"period": date(2024, 1, 1), "value": 148000},
        {"period": date(2024, 2, 1), "value": 151000},
        {"period": date(2024, 3, 1), "value": 155000},
        {"period": date(2024, 4, 1), "value": 160000},
        {"period": date(2024, 5, 1), "value": 164000},
        {"period": date(2024, 6, 1), "value": 167000},
    ],
    "plc_summit_ridge_golf": [
        {"period": date(2024, 1, 1), "value": 21000},
        {"period": date(2024, 2, 1), "value": 24000},
        {"period": date(2024, 3, 1), "value": 42000},
        {"period": date(2024, 4, 1), "value": 56000},
        {"period": date(2024, 5, 1), "value": 72000},
        {"period": date(2024, 6, 1), "value": 78000},
    ],
    "plc_riverbend_plaza": [
        {"period": date(2024, 1, 1), "value": 48000},
        {"period": date(2024, 2, 1), "value": 50000},
        {"period": date(2024, 3, 1), "value": 52000},
        {"period": date(2024, 4, 1), "value": 54000},
        {"period": date(2024, 5, 1), "value": 56000},
        {"period": date(2024, 6, 1), "value": 58000},
    ],
    "plc_quickmart_lakeview": [
        {"period": date(2024, 1, 1), "value": 21000},
        {"period": date(2024, 2, 1), "value": 21500},
        {"period": date(2024, 3, 1), "value": 22000},
        {"period": date(2024, 4, 1), "value": 23000},
        {"period": date(2024, 5, 1), "value": 24000},
        {"period": date(2024, 6, 1), "value": 25500},
    ],
    "plc_freshmart_aurora": [
        {"period": date(2024, 1, 1), "value": 56000},
        {"period": date(2024, 2, 1), "value": 57000},
        {"period": date(2024, 3, 1), "value": 59000},
        {"period": date(2024, 4, 1), "value": 61000},
        {"period": date(2024, 5, 1), "value": 64000},
        {"period": date(2024, 6, 1), "value": 66000},
    ],
    "plc_lakeview_taphouse": [
        {"period": date(2024, 1, 1), "value": 15000},
        {"period": date(2024, 2, 1), "value": 16000},
        {"period": date(2024, 3, 1), "value": 17500},
        {"period": date(2024, 4, 1), "value": 19000},
        {"period": date(2024, 5, 1), "value": 20500},
        {"period": date(2024, 6, 1), "value": 21500},
    ],
}

VISIT_FREQUENCY_SERIES = {
    place_id: [
        {"period": entry["period"], "value": round(1.2 + idx * 0.05, 2)}
        for idx, entry in enumerate(series)
    ]
    for place_id, series in VISIT_SERIES.items()
}

DWELL_TIME_SERIES = {
    place_id: [
        {"period": entry["period"], "value": 60 + idx * 3 + hash(place_id) % 5}
        for idx, entry in enumerate(series)
    ]
    for place_id, series in VISIT_SERIES.items()
}

PLACE_SUMMARY = {
    "plc_northwood_town_center": {
        "unique_visitors": 245000,
        "median_dwell": 82,
    },
    "plc_summit_ridge_golf": {
        "unique_visitors": 72000,
        "median_dwell": 134,
    },
    "plc_riverbend_plaza": {
        "unique_visitors": 112000,
        "median_dwell": 64,
    },
    "plc_quickmart_lakeview": {
        "unique_visitors": 54000,
        "median_dwell": 18,
    },
    "plc_freshmart_aurora": {
        "unique_visitors": 128000,
        "median_dwell": 52,
    },
    "plc_lakeview_taphouse": {
        "unique_visitors": 41000,
        "median_dwell": 96,
    },
}

AUDIENCE_DATA = {
    "plc_northwood_town_center": {
        "age_distribution": {"18-24": 0.11, "25-34": 0.23, "35-44": 0.21, "45-54": 0.18, "55-64": 0.15, "65+": 0.12},
        "income_distribution": {"<50k": 0.22, "50-75k": 0.24, "75-100k": 0.2, "100-150k": 0.2, "150k+": 0.14},
        "household_size_distribution": {"1": 0.18, "2": 0.31, "3": 0.23, "4+": 0.28},
        "presence_of_kids_pct": 0.44,
        "lifestyle_segments": [
            {"name": "Active Families", "share_of_visitors": 0.32},
            {"name": "Suburban Professionals", "share_of_visitors": 0.28},
            {"name": "Value Seekers", "share_of_visitors": 0.24},
        ],
        "visit_frequency_profile": {"weekly": 0.28, "monthly": 0.52, "quarterly": 0.2},
    },
    "plc_summit_ridge_golf": {
        "age_distribution": {"18-24": 0.07, "25-34": 0.18, "35-44": 0.26, "45-54": 0.23, "55-64": 0.17, "65+": 0.09},
        "income_distribution": {"<50k": 0.12, "50-75k": 0.2, "75-100k": 0.23, "100-150k": 0.25, "150k+": 0.2},
        "household_size_distribution": {"1": 0.16, "2": 0.38, "3": 0.24, "4+": 0.22},
        "presence_of_kids_pct": 0.38,
        "lifestyle_segments": [
            {"name": "Golf Enthusiasts", "share_of_visitors": 0.41},
            {"name": "Affluent Couples", "share_of_visitors": 0.27},
            {"name": "Outdoor Weekenders", "share_of_visitors": 0.19},
        ],
        "visit_frequency_profile": {"weekly": 0.22, "monthly": 0.48, "quarterly": 0.3},
    },
    "plc_riverbend_plaza": {
        "age_distribution": {"18-24": 0.12, "25-34": 0.24, "35-44": 0.22, "45-54": 0.2, "55-64": 0.13, "65+": 0.09},
        "income_distribution": {"<50k": 0.3, "50-75k": 0.28, "75-100k": 0.19, "100-150k": 0.15, "150k+": 0.08},
        "household_size_distribution": {"1": 0.2, "2": 0.36, "3": 0.26, "4+": 0.18},
        "presence_of_kids_pct": 0.41,
        "lifestyle_segments": [
            {"name": "Budget Families", "share_of_visitors": 0.37},
            {"name": "Young Singles", "share_of_visitors": 0.21},
            {"name": "Local Errand Runners", "share_of_visitors": 0.19},
        ],
        "visit_frequency_profile": {"weekly": 0.33, "monthly": 0.49, "quarterly": 0.18},
    },
    "plc_quickmart_lakeview": {
        "age_distribution": {"18-24": 0.19, "25-34": 0.31, "35-44": 0.18, "45-54": 0.15, "55-64": 0.1, "65+": 0.07},
        "income_distribution": {"<50k": 0.34, "50-75k": 0.27, "75-100k": 0.18, "100-150k": 0.13, "150k+": 0.08},
        "household_size_distribution": {"1": 0.44, "2": 0.3, "3": 0.16, "4+": 0.1},
        "presence_of_kids_pct": 0.28,
        "lifestyle_segments": [
            {"name": "Urban Errand Runners", "share_of_visitors": 0.39},
            {"name": "Young Professionals", "share_of_visitors": 0.33},
            {"name": "Night Owls", "share_of_visitors": 0.18},
        ],
        "visit_frequency_profile": {"weekly": 0.46, "monthly": 0.42, "quarterly": 0.12},
    },
    "plc_freshmart_aurora": {
        "age_distribution": {"18-24": 0.1, "25-34": 0.23, "35-44": 0.24, "45-54": 0.2, "55-64": 0.13, "65+": 0.1},
        "income_distribution": {"<50k": 0.26, "50-75k": 0.27, "75-100k": 0.2, "100-150k": 0.17, "150k+": 0.1},
        "household_size_distribution": {"1": 0.19, "2": 0.34, "3": 0.28, "4+": 0.19},
        "presence_of_kids_pct": 0.46,
        "lifestyle_segments": [
            {"name": "Family Meal Planners", "share_of_visitors": 0.36},
            {"name": "Health Conscious", "share_of_visitors": 0.27},
            {"name": "Value Shoppers", "share_of_visitors": 0.21},
        ],
        "visit_frequency_profile": {"weekly": 0.39, "monthly": 0.45, "quarterly": 0.16},
    },
    "plc_lakeview_taphouse": {
        "age_distribution": {"18-24": 0.22, "25-34": 0.36, "35-44": 0.19, "45-54": 0.12, "55-64": 0.07, "65+": 0.04},
        "income_distribution": {"<50k": 0.31, "50-75k": 0.3, "75-100k": 0.19, "100-150k": 0.13, "150k+": 0.07},
        "household_size_distribution": {"1": 0.48, "2": 0.32, "3": 0.13, "4+": 0.07},
        "presence_of_kids_pct": 0.17,
        "lifestyle_segments": [
            {"name": "Nightlife Regulars", "share_of_visitors": 0.44},
            {"name": "Foodies", "share_of_visitors": 0.28},
            {"name": "After-Work Groups", "share_of_visitors": 0.18},
        ],
        "visit_frequency_profile": {"weekly": 0.41, "monthly": 0.4, "quarterly": 0.19},
    },
    "chn_quickmart": {
        "age_distribution": {"18-24": 0.18, "25-34": 0.32, "35-44": 0.2, "45-54": 0.16, "55-64": 0.09, "65+": 0.05},
        "income_distribution": {"<50k": 0.36, "50-75k": 0.27, "75-100k": 0.18, "100-150k": 0.12, "150k+": 0.07},
        "household_size_distribution": {"1": 0.4, "2": 0.33, "3": 0.16, "4+": 0.11},
        "presence_of_kids_pct": 0.26,
        "lifestyle_segments": [
            {"name": "Urban Errand Runners", "share_of_visitors": 0.42},
            {"name": "Shift Workers", "share_of_visitors": 0.23},
            {"name": "Value Seekers", "share_of_visitors": 0.2},
        ],
        "visit_frequency_profile": {"weekly": 0.5, "monthly": 0.37, "quarterly": 0.13},
    },
    "chn_freshmart": {
        "age_distribution": {"18-24": 0.11, "25-34": 0.24, "35-44": 0.25, "45-54": 0.2, "55-64": 0.12, "65+": 0.08},
        "income_distribution": {"<50k": 0.24, "50-75k": 0.28, "75-100k": 0.21, "100-150k": 0.17, "150k+": 0.1},
        "household_size_distribution": {"1": 0.21, "2": 0.33, "3": 0.27, "4+": 0.19},
        "presence_of_kids_pct": 0.48,
        "lifestyle_segments": [
            {"name": "Family Meal Planners", "share_of_visitors": 0.34},
            {"name": "Health Conscious", "share_of_visitors": 0.29},
            {"name": "Value Shoppers", "share_of_visitors": 0.22},
        ],
        "visit_frequency_profile": {"weekly": 0.41, "monthly": 0.44, "quarterly": 0.15},
    },
}

AUDIENCE_BASELINES = {
    "region_chicago": {
        "age_distribution": {"18-24": 0.13, "25-34": 0.23, "35-44": 0.21, "45-54": 0.19, "55-64": 0.14, "65+": 0.1},
        "income_distribution": {"<50k": 0.3, "50-75k": 0.27, "75-100k": 0.19, "100-150k": 0.15, "150k+": 0.09},
    }
}

VISITOR_OVERLAP = {
    ("plc_summit_ridge_golf", "plc_quickmart_lakeview"): 0.34,
    ("plc_summit_ridge_golf", "plc_lakeview_taphouse"): 0.27,
    ("plc_summit_ridge_golf", "plc_freshmart_aurora"): 0.19,
    ("plc_northwood_town_center", "plc_riverbend_plaza"): 0.42,
    ("plc_northwood_town_center", "plc_freshmart_aurora"): 0.33,
    ("plc_riverbend_plaza", "plc_quickmart_lakeview"): 0.29,
}

JOURNEY_FLOWS = {
    "plc_summit_ridge_golf": [
        {
            "destination": {"type": "place", "id": "plc_quickmart_lakeview", "name": PLACES["plc_quickmart_lakeview"]["name"]},
            "shared_visitors": 5200,
            "visits": 11800,
            "share_of_origin_visitors": 0.31,
            "median_time_offset_minutes": 42,
        },
        {
            "destination": {"type": "place", "id": "plc_lakeview_taphouse", "name": PLACES["plc_lakeview_taphouse"]["name"]},
            "shared_visitors": 4100,
            "visits": 9300,
            "share_of_origin_visitors": 0.24,
            "median_time_offset_minutes": 95,
        },
        {
            "destination": {"type": "place", "id": "plc_freshmart_aurora", "name": PLACES["plc_freshmart_aurora"]["name"]},
            "shared_visitors": 3600,
            "visits": 8200,
            "share_of_origin_visitors": 0.21,
            "median_time_offset_minutes": -37,
        },
    ],
    "plc_northwood_town_center": [
        {
            "destination": {"type": "place", "id": "plc_riverbend_plaza", "name": PLACES["plc_riverbend_plaza"]["name"]},
            "shared_visitors": 18200,
            "visits": 38100,
            "share_of_origin_visitors": 0.38,
            "median_time_offset_minutes": 63,
        },
        {
            "destination": {"type": "place", "id": "plc_freshmart_aurora", "name": PLACES["plc_freshmart_aurora"]["name"]},
            "shared_visitors": 15500,
            "visits": 32500,
            "share_of_origin_visitors": 0.32,
            "median_time_offset_minutes": -45,
        },
    ],
}

TRADE_AREA_DATA = {
    "plc_summit_ridge_golf": {
        "trade_area_polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-88.05, 41.87],
                    [-87.96, 41.87],
                    [-87.96, 41.92],
                    [-88.05, 41.92],
                    [-88.05, 41.87],
                ]
            ],
        },
        "geo_units": [
            {
                "id": "zip_60523",
                "visits": 15000,
                "share_of_visits": 0.32,
                "avg_distance_km": 8.4,
                "demographics": {"median_income": 112000, "household_size": 2.7},
                "psychographics": {"top_segment": "Active Suburban"},
            },
            {
                "id": "zip_60515",
                "visits": 9200,
                "share_of_visits": 0.2,
                "avg_distance_km": 11.3,
                "demographics": {"median_income": 98000, "household_size": 2.6},
                "psychographics": {"top_segment": "Young Families"},
            },
            {
                "id": "zip_60527",
                "visits": 8600,
                "share_of_visits": 0.18,
                "avg_distance_km": 9.7,
                "demographics": {"median_income": 104000, "household_size": 2.8},
                "psychographics": {"top_segment": "Outdoor Lifestyles"},
            },
        ],
    },
    "plc_northwood_town_center": {
        "trade_area_polygon": {
            "type": "Polygon",
            "coordinates": [
                [
                    [-87.75, 41.89],
                    [-87.65, 41.89],
                    [-87.65, 41.94],
                    [-87.75, 41.94],
                    [-87.75, 41.89],
                ]
            ],
        },
        "geo_units": [
            {
                "id": "zip_60640",
                "visits": 42000,
                "share_of_visits": 0.28,
                "avg_distance_km": 4.1,
                "demographics": {"median_income": 78000, "household_size": 2.2},
                "psychographics": {"top_segment": "Young Urban"},
            },
            {
                "id": "zip_60657",
                "visits": 39000,
                "share_of_visits": 0.26,
                "avg_distance_km": 3.2,
                "demographics": {"median_income": 91000, "household_size": 2.0},
                "psychographics": {"top_segment": "Dual Income"},
            },
            {
                "id": "zip_60707",
                "visits": 31000,
                "share_of_visits": 0.2,
                "avg_distance_km": 6.8,
                "demographics": {"median_income": 72000, "household_size": 2.6},
                "psychographics": {"top_segment": "Value Seekers"},
            },
        ],
    },
}
