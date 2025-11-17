from __future__ import annotations

import json

from .repository import DATA_REPOSITORY


def search_places(
    geo_filter_type: str,
    geo_config: str,
    category_ids: str = "",
    chain_ids: str = "",
    text_query: str = "",
    portfolio_tags: str = "",
    min_visits: int = 0,
    limit: int = 25,
) -> str:
    """
    Discover places (POIs/properties) based on geography and filters.

    This is the foundational catalog discovery tool. Use it to find:
    - Candidate sites and comps in a metro (Real Estate)
    - Centers in a region or owned portfolio (Asset Management)
    - Lists of stores for media campaigns (Retail Media)
    - Golf courses and nearby outlets (Consumer Insights)

    Args:
        geo_filter_type (str): Type of geographic filter. Must be one of:
            - "point_radius": circular area around lat/lon
            - "bounding_box": rectangular bounds
            - "polygon": custom polygon shape
            - "metro": predefined metropolitan area
        geo_config (str): JSON string with geography config. Format depends on geo_filter_type:
            - point_radius: {"lat": 40.9, "lon": -74.1, "radius_km": 15}
            - metro: {"name": "nyc"} or {"name": "atlanta"}
            - bounding_box: {"lat_min": 40.0, "lat_max": 41.0, "lon_min": -75.0, "lon_max": -74.0}
            - polygon: {"coordinates": [[lon1,lat1], [lon2,lat2], ...]}
        category_ids (str): Comma-separated category IDs (e.g., "regional_mall,fast_casual,golf_course")
        chain_ids (str): Comma-separated chain IDs to filter by specific brands
        text_query (str): Search by name (e.g., "Chick-fil-A", "Garden State Plaza")
        portfolio_tags (str): Comma-separated tags (e.g., "our_stores,our_centers,priority_outlet")
        min_visits (int): Minimum annual visits threshold (default 0)
        limit (int): Maximum number of results to return (default 25)

    Returns:
        str: JSON string with array of matching places, or None if error occurs
    """
    try:
        geo_config_dict = json.loads(geo_config)
        geo_filter = {"type": geo_filter_type, "config": geo_config_dict}

        places = DATA_REPOSITORY.search_places(
            geo_filter=geo_filter,
            category_ids=category_ids.split(",") if category_ids else None,
            chain_ids=chain_ids.split(",") if chain_ids else None,
            text_query=text_query if text_query else None,
            portfolio_tags=portfolio_tags.split(",") if portfolio_tags else None,
            min_visits=min_visits if min_visits > 0 else None,
            limit=limit,
        )

        return json.dumps({"places": places})
    except Exception:
        return json.dumps({"places": [], "error": "Failed to search places"})


def get_place_summary(
    place_ids: str,
    time_range_start: str,
    time_range_end: str,
    granularity: str = "monthly",
    include_benchmark: bool = False,
    include_rollup: bool = False,
) -> str:
    """
    Get health and context snapshot for one or more places.

    Returns visit patterns, trends, and competitive positioning.
    This is typically the first tool called once you know which place(s) matter.

    Use cases:
    - Compare candidate vs comp store performance (Real Estate)
    - Check center health and trends (Asset Management)
    - Sanity-check stores before adding to campaigns (Retail Media)
    - Get outlet-level context around target locations (Consumer Insights)

    Args:
        place_ids (str): Comma-separated place IDs to analyze
        time_range_start (str): Start date in YYYY-MM-DD format
        time_range_end (str): End date in YYYY-MM-DD format
        granularity (str): Time bucket size. Must be one of:
            - "daily": day-by-day data
            - "weekly": week-by-week data
            - "monthly": month-by-month data (default)
        include_benchmark (bool): If true, compare vs category/region baseline (default false)
        include_rollup (bool): If true, include aggregated stats across all places (default false)

    Returns:
        str: JSON string with place summaries, or None if error occurs
    """
    try:
        from datetime import date

        place_list = place_ids.split(",")
        time_dict = {
            "start": date.fromisoformat(time_range_start),
            "end": date.fromisoformat(time_range_end),
        }

        summaries = []
        for place_id in place_list:
            place = DATA_REPOSITORY.get_place(place_id)
            series = DATA_REPOSITORY.place_series(place_id, time_dict)
            total_visits = sum(row["visits"] for row in series)

            summary = {
                "place": place,
                "visits": {
                    "total": total_visits,
                    "by_period": series,
                    "granularity": granularity,
                },
                "unique_visitors": place["unique_visitors"],
                "visit_frequency": place["visit_frequency"],
                "dwell_time": {"median_minutes": place["dwell_minutes"]},
                "trend": {
                    "yoy_change_pct": place.get("yoy_change_pct"),
                    "mom_change_pct": place.get("mom_change_pct"),
                    "classification": place.get("classification"),
                },
            }

            if include_benchmark:
                summary["benchmark"] = {"index": DATA_REPOSITORY.benchmark_index(place)}

            summaries.append(summary)

        payload = {"places": summaries}

        if include_rollup:
            aggregate = DATA_REPOSITORY.aggregate_places(place_list, time_dict)
            payload["rollup"] = aggregate

        return json.dumps(payload)
    except Exception:
        return json.dumps({"places": [], "error": "Failed to get place summary"})


def compare_performance(
    entities: str, time_range_start: str, time_range_end: str, metric: str = "visits"
) -> str:
    """
    Compare time-series performance of multiple locations or chains.

    Powers portfolio views and "who's winning/losing" questions by ranking
    and classifying entities.

    Use cases:
    - Market or chain-wide ranking for stores (Real Estate)
    - Portfolio health, top/bottom centers (Asset Management)
    - Find fast-growing stores for RMN (Retail Media)
    - Post-launch outlet monitoring (Consumer Insights)

    Args:
        entities (str): JSON string with array of entities: [{"type": "place", "id": "place_123"}, ...]
        time_range_start (str): Start date in YYYY-MM-DD format
        time_range_end (str): End date in YYYY-MM-DD format
        metric (str): Performance metric to compare. Must be one of:
            - "visits": total visit counts (default)
            - "visit_frequency": avg visits per unique visitor
            - "dwell_time": median time spent in minutes

    Returns:
        str: JSON string with performance series and rankings, or None if error occurs
    """
    try:
        from datetime import date

        entity_list = json.loads(entities)
        time_dict = {
            "start": date.fromisoformat(time_range_start),
            "end": date.fromisoformat(time_range_end),
        }

        series_payload = []
        ranked_values = []

        for entity in entity_list:
            entity_type = entity["type"]
            entity_id = entity["id"]

            if entity_type == "place":
                place = DATA_REPOSITORY.get_place(entity_id)
                series = DATA_REPOSITORY.place_series(entity_id, time_dict)
                total_value = sum(row["visits"] for row in series)

                series_payload.append(
                    {
                        "entity": {
                            "type": entity_type,
                            "id": entity_id,
                            "name": place["name"],
                        },
                        "by_period": series,
                        "yoy_change_pct": place.get("yoy_change_pct"),
                        "classification": place.get("classification", "stable"),
                    }
                )

                ranked_values.append({"id": entity_id, "value": total_value})

        ranked_values.sort(key=lambda x: x["value"], reverse=True)
        rankings = [
            {
                "metric": metric,
                "ranked_entities": [
                    {"id": item["id"], "value": item["value"], "rank": idx + 1}
                    for idx, item in enumerate(ranked_values)
                ],
            }
        ]

        return json.dumps({"series": series_payload, "rankings": rankings})
    except Exception:
        return json.dumps(
            {"series": [], "rankings": [], "error": "Failed to compare performance"}
        )


def get_trade_area_profile(
    place_ids: str,
    time_range_start: str,
    time_range_end: str,
    output_geography: str = "census_tract",
) -> str:
    """
    Describe the "True Trade Area" of one or more places.

    Shows where visitors come from, how important each geography is,
    and who those visitors are (demographics, income, household profile).

    Use cases:
    - Cannibalization risk and white space/infill analysis (Real Estate)
    - Catchment quality and repositioning (Asset Management)
    - Geo/audience fit for campaigns (Retail Media)
    - Trade areas around golf courses and nearby outlets (Consumer Insights)

    Args:
        place_ids (str): Comma-separated place IDs to analyze
        time_range_start (str): Start date in YYYY-MM-DD format
        time_range_end (str): End date in YYYY-MM-DD format
        output_geography (str): Geographic unit level. Must be one of:
            - "block_group": Census block group level
            - "census_tract": Census tract level (default)
            - "zip": ZIP code level
            - "cbg": Core-based statistical area

    Returns:
        str: JSON string with trade area profiles, or None if error occurs
    """
    try:
        place_list = place_ids.split(",")

        profiles = []
        for place_id in place_list:
            trade_area = DATA_REPOSITORY.get_trade_area(place_id)
            if trade_area:
                profiles.append(
                    {
                        "place_id": place_id,
                        "trade_area_polygon": trade_area.get("trade_area_polygon"),
                        "geo_units": trade_area.get("geo_units", []),
                        "summary": trade_area.get("summary", {}),
                        "output_geography": output_geography,
                    }
                )

        return json.dumps({"profiles": profiles})
    except Exception:
        return json.dumps({"profiles": [], "error": "Failed to get trade area profile"})


def get_audience_profile(
    base_entities: str,
    time_range_start: str,
    time_range_end: str,
    dimensions: str = "age,income",
) -> str:
    """
    Describe who visits a place/chain and how that audience overlaps or differs from others.

    Returns demographics, income, households, lifestyle, and audience similarity/overlap indices.

    Use cases:
    - Tenant/site audience fit analysis (Real Estate)
    - Asset repositioning and target mix validation (Asset Management)
    - Audience-based store bundling and campaign targeting (Retail Media)
    - Whether golf visitors match target segment for a product (Consumer Insights)

    Args:
        base_entities (str): JSON string with base entities: [{"type": "place", "id": "place_123"}, ...]
        time_range_start (str): Start date in YYYY-MM-DD format
        time_range_end (str): End date in YYYY-MM-DD format
        dimensions (str): Comma-separated dimensions to analyze. Options:
            - "age": age distribution
            - "income": income brackets
            - "household_size": household size distribution
            - "kids": presence of children
            - "lifestyle": lifestyle/interest segments
            - "visit_frequency": visit pattern analysis

    Returns:
        str: JSON string with audience profiles, or None if error occurs
    """
    try:
        entity_list = json.loads(base_entities)
        dimension_list = dimensions.split(",")

        results = []
        for entity in entity_list:
            entity_type = entity["type"]
            entity_id = entity["id"]

            profile = DATA_REPOSITORY.entity_profile(entity_type, entity_id)

            profile_data = {}
            if "age" in dimension_list:
                profile_data["age_distribution"] = profile.get("age_distribution", {})
            if "income" in dimension_list:
                profile_data["income_distribution"] = profile.get(
                    "income_distribution", {}
                )

            results.append(
                {
                    "entity": {"type": entity_type, "id": entity_id},
                    "profile": profile_data,
                }
            )

        return json.dumps({"results": results})
    except Exception:
        return json.dumps({"results": [], "error": "Failed to get audience profile"})


def get_visit_flows(
    origin_place_ids: str,
    time_range_start: str,
    time_range_end: str,
    window_before_minutes: int = 120,
    window_after_minutes: int = 240,
    group_by: str = "destination_place",
) -> str:
    """
    Understand visit flows before and after a visit to a given origin.

    Reveals cross-shopping behavior, path-to-purchase patterns, and co-tenancy synergies.

    Use cases:
    - Golf → convenience/bar path for product placement (Consumer Insights)
    - Spillover to partner brands for co-marketing (Retail Media)
    - Co-tenancy insights - what pairs well together (Real Estate & Asset Management)

    Args:
        origin_place_ids (str): Comma-separated origin place IDs to analyze
        time_range_start (str): Start date in YYYY-MM-DD format
        time_range_end (str): End date in YYYY-MM-DD format
        window_before_minutes (int): Minutes before origin visit to look for flows (default 120)
        window_after_minutes (int): Minutes after origin visit to look for flows (default 240)
        group_by (str): How to group destinations. Must be one of:
            - "destination_place": individual place level (default)
            - "destination_chain": chain/brand level
            - "destination_category": category level

    Returns:
        str: JSON string with visit flow data, or None if error occurs
    """
    try:
        place_list = origin_place_ids.split(",")

        origins_payload = []
        for origin_id in place_list:
            flows = DATA_REPOSITORY.flows_for_origin(origin_id)

            filtered_flows = []
            for flow in flows:
                offset = flow.get("median_time_offset_minutes", 0)
                if offset < 0 and abs(offset) <= window_before_minutes:
                    filtered_flows.append(flow)
                elif offset > 0 and offset <= window_after_minutes:
                    filtered_flows.append(flow)

            origins_payload.append(
                {"origin_place_id": origin_id, "flows_out": filtered_flows[:10]}
            )

        return json.dumps({"origins": origins_payload})
    except Exception:
        return json.dumps({"origins": [], "error": "Failed to get visit flows"})
