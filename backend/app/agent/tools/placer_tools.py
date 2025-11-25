from typing import Any

from pydantic import BaseModel, Field


# ============================================================================
# Tool Input Models (Pydantic for validation)
# ============================================================================


class SearchPlacesInput(BaseModel):
    geo_filter: dict = Field(
        ...,
        description="Geography filter: {type: 'point_radius'|'bounding_box'|'polygon'|'metro', config: {...}}",
    )
    category_ids: list[str] | None = Field(
        None, description="Category IDs (e.g., NAICS codes or internal taxonomy)"
    )
    chain_ids: list[str] | None = Field(None, description="Chain/brand IDs")
    text_query: str | None = Field(
        None, description="Text search (e.g., 'Chick-fil-A', 'Garden State Plaza')"
    )
    portfolio_tags: list[str] | None = Field(
        None, description="Portfolio tags (e.g., 'our_stores', 'our_centers')"
    )
    min_visits: int | None = Field(None, description="Minimum monthly visits")
    limit: int = Field(10, description="Maximum number of results to return")


class GetPlaceSummaryInput(BaseModel):
    place_ids: list[str] = Field(..., description="List of place IDs to summarize")
    time_range: dict = Field(
        ..., description="Time range: {start: 'YYYY-MM-DD', end: 'YYYY-MM-DD'}"
    )
    granularity: str = Field(
        "monthly", description="Data granularity: 'daily', 'weekly', 'monthly'"
    )
    include_benchmark: bool = Field(
        True, description="Include category benchmark comparison"
    )


class CompareLocationsInput(BaseModel):
    entities: list[dict] = Field(
        ...,
        description="Entities to compare: [{type: 'place'|'chain'|'category', id: str}]",
    )
    time_range: dict = Field(
        ..., description="Time range: {start: 'YYYY-MM-DD', end: 'YYYY-MM-DD'}"
    )
    metric: str = Field(
        "visits", description="Metric to compare: 'visits', 'unique_visitors', etc."
    )
    include_ranking: bool = Field(True, description="Include performance ranking")


class GetTradeAreaProfileInput(BaseModel):
    place_ids: list[str] = Field(..., description="Place IDs to analyze")
    time_range: dict = Field(
        ..., description="Time range: {start: 'YYYY-MM-DD', end: 'YYYY-MM-DD'}"
    )
    output_geography: str = Field(
        "zip", description="Output geography level: 'zip', 'county', 'cbsa'"
    )
    include_demographics: bool = Field(True, description="Include demographic data")
    max_radius_km: float | None = Field(
        None, description="Maximum radius for trade area analysis"
    )


class GetProfileAndOverlapInput(BaseModel):
    base_entities: list[dict] = Field(
        ..., description="Base entities: [{type: 'place'|'chain', id: str}]"
    )
    comparison_entities: list[dict] | None = Field(
        None, description="Entities to compare against"
    )
    time_range: dict = Field(
        ..., description="Time range: {start: 'YYYY-MM-DD', end: 'YYYY-MM-DD'}"
    )
    dimensions: list[str] = Field(
        ["age", "income"],
        description="Demographic dimensions: 'age', 'income', 'household', etc.",
    )


class GetVisitFlowsInput(BaseModel):
    origin_place_ids: list[str] = Field(
        ..., description="Origin place IDs for journey analysis"
    )
    time_range: dict = Field(
        ..., description="Time range: {start: 'YYYY-MM-DD', end: 'YYYY-MM-DD'}"
    )
    window_before_minutes: int = Field(
        120, description="Time window before visit (minutes)"
    )
    window_after_minutes: int = Field(
        120, description="Time window after visit (minutes)"
    )
    group_by: str = Field(
        "chain", description="Group destinations by: 'place', 'chain', 'category'"
    )
    min_shared_visitors: int = Field(
        100, description="Minimum shared visitors for destination inclusion"
    )


# ============================================================================
# Tool Implementations
# ============================================================================


class SearchPlacesTool:
    """Discover POIs/properties by geography and filters"""

    name = "search_places"
    description = """Discover places (POIs/properties) by geography and filters.

    Use this foundational tool for:
    - Finding candidate sites and comps in a metro
    - Enumerating centers/stores in a region or portfolio
    - Listing stores for analysis
    - Discovering golf courses, malls, restaurants, etc.

    Examples:
    - "Find Starbucks in San Francisco"
    - "Show me all shopping malls in Los Angeles"
    - "List Chick-fil-A locations in Atlanta"
    """

    def get_input_schema(self) -> dict:
        return SearchPlacesInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        try:
            input_data = SearchPlacesInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "places": [],
                "total": 0,
            }

        # Mock data - realistic POI results
        mock_places = [
            {
                "id": "place_sf_001",
                "name": "Starbucks Reserve Roastery",
                "address": "199 Fremont St, San Francisco, CA 94105",
                "lat": 37.7897,
                "lon": -122.3972,
                "category_id": "coffee_shop",
                "chain_id": "starbucks",
                "tags": ["premium", "high_traffic", "downtown"],
            },
            {
                "id": "place_sf_002",
                "name": "Blue Bottle Coffee",
                "address": "66 Mint St, San Francisco, CA 94103",
                "lat": 37.7794,
                "lon": -122.4078,
                "category_id": "coffee_shop",
                "chain_id": "blue_bottle",
                "tags": ["artisanal", "tech_crowd"],
            },
            {
                "id": "place_sf_003",
                "name": "Philz Coffee",
                "address": "201 Berry St, San Francisco, CA 94158",
                "lat": 37.7764,
                "lon": -122.3926,
                "category_id": "coffee_shop",
                "chain_id": "philz",
                "tags": ["local", "mission_bay"],
            },
        ]

        return {
            "places": mock_places[: input_data.limit],
            "total": len(mock_places),
            "query_metadata": {
                "geo_type": input_data.geo_filter.get("type"),
                "filters_applied": [
                    f
                    for f in ["geo", "category", "chain", "text"]
                    if getattr(
                        input_data, f"{f}_ids" if f != "geo" else "geo_filter", None
                    )
                    or input_data.text_query
                ],
            },
        }


class GetPlaceSummaryTool:
    """Get health metrics and performance summary for places"""

    name = "get_place_summary"
    description = """Get performance metrics and health snapshot for specific places.

    Returns:
    - Visit counts and trends
    - Unique visitor metrics
    - Visit frequency and dwell time
    - Performance classifications (Growing, Stable, Declining)
    - Category benchmarks

    Use after search_places to get detailed metrics."""

    def get_input_schema(self) -> dict:
        return GetPlaceSummaryInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        try:
            input_data = GetPlaceSummaryInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "summaries": [],
            }

        # Mock data - realistic performance metrics
        summaries = []
        for place_id in input_data.place_ids:
            summaries.append(
                {
                    "place_id": place_id,
                    "metrics": {
                        "monthly_visits": 12500,
                        "unique_visitors": 8200,
                        "visit_frequency": 1.52,
                        "avg_dwell_minutes": 22,
                    },
                    "trends": {
                        "mom_change": 5.2,
                        "yoy_change": 12.8,
                        "classification": "Growing",
                    },
                    "benchmark": {
                        "category_avg_visits": 10000,
                        "percentile": 68,
                    }
                    if input_data.include_benchmark
                    else None,
                }
            )

        return {
            "summaries": summaries,
            "time_range": input_data.time_range,
            "granularity": input_data.granularity,
        }


class CompareLocationsTool:
    """Compare multiple locations with time-series data and rankings"""

    name = "compare_locations"
    description = """Compare performance across multiple locations or entities.

    Use for:
    - Portfolio analysis and ranking
    - Site selection comparisons
    - Competitive benchmarking
    - Time-series trend analysis

    Returns rankings, time-series data, and performance classifications."""

    def get_input_schema(self) -> dict:
        return CompareLocationsInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        try:
            input_data = CompareLocationsInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "comparisons": [],
            }

        # Mock comparison data
        comparisons = []
        for idx, entity in enumerate(input_data.entities):
            comparisons.append(
                {
                    "entity": entity,
                    "current_value": 15000 - (idx * 2000),
                    "mom_change": 3.5 - (idx * 0.5),
                    "yoy_change": 10.2 - (idx * 1.5),
                    "rank": idx + 1 if input_data.include_ranking else None,
                    "classification": ["Growing", "Stable", "Declining"][idx % 3],
                    "time_series": [
                        {"period": "2024-10", "value": 14000 - (idx * 2000)},
                        {"period": "2024-11", "value": 14500 - (idx * 2000)},
                        {"period": "2024-12", "value": 15000 - (idx * 2000)},
                    ],
                }
            )

        return {
            "comparisons": comparisons,
            "metric": input_data.metric,
            "time_range": input_data.time_range,
        }


class GetTradeAreaProfileTool:
    """Analyze visitor origin geography and demographics"""

    name = "get_trade_area_profile"
    description = """Get trade area profile showing where visitors come from and demographics.

    Returns:
    - Geographic distribution of visitor origins
    - Trade area polygons
    - Demographic profiles of visitor base
    - Distance/travel time analysis

    Use for understanding catchment areas and customer base."""

    def get_input_schema(self) -> dict:
        return GetTradeAreaProfileInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        try:
            input_data = GetTradeAreaProfileInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "trade_areas": [],
            }

        # Mock trade area data
        trade_areas = []
        for place_id in input_data.place_ids:
            trade_areas.append(
                {
                    "place_id": place_id,
                    "geographic_distribution": [
                        {
                            "geo_id": "94105",
                            "geo_name": "San Francisco Downtown",
                            "visit_share": 35.2,
                            "avg_distance_km": 2.1,
                        },
                        {
                            "geo_id": "94107",
                            "geo_name": "San Francisco SOMA",
                            "visit_share": 22.8,
                            "avg_distance_km": 3.5,
                        },
                        {
                            "geo_id": "94103",
                            "geo_name": "San Francisco Mission",
                            "visit_share": 18.5,
                            "avg_distance_km": 4.2,
                        },
                    ],
                    "demographics": {
                        "median_age": 34,
                        "median_income": 95000,
                        "household_size_avg": 2.1,
                    }
                    if input_data.include_demographics
                    else None,
                }
            )

        return {
            "trade_areas": trade_areas,
            "time_range": input_data.time_range,
            "output_geography": input_data.output_geography,
        }


class GetProfileAndOverlapTool:
    """Analyze visitor demographics and audience overlap"""

    name = "get_profile_and_overlap"
    description = """Get detailed visitor demographics and audience overlap analysis.

    Returns:
    - Age, income, household distributions
    - Lifestyle and interest profiles
    - Audience overlap indices between entities
    - Affinity scores

    Use for tenant fit analysis, RMN audience bundling, and customer profiling."""

    def get_input_schema(self) -> dict:
        return GetProfileAndOverlapInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        try:
            input_data = GetProfileAndOverlapInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "profiles": [],
                "overlaps": None,
            }

        # Mock demographic profile
        profiles = []
        for entity in input_data.base_entities:
            profile = {
                "entity": entity,
                "demographics": {},
            }

            if "age" in input_data.dimensions:
                profile["demographics"]["age"] = {
                    "18-24": 12.5,
                    "25-34": 28.3,
                    "35-44": 24.7,
                    "45-54": 18.2,
                    "55-64": 10.8,
                    "65+": 5.5,
                }

            if "income" in input_data.dimensions:
                profile["demographics"]["income"] = {
                    "<$25k": 5.2,
                    "$25-50k": 12.8,
                    "$50-75k": 18.5,
                    "$75-100k": 22.3,
                    "$100-150k": 25.7,
                    "$150k+": 15.5,
                }

            profiles.append(profile)

        # Mock overlap analysis
        overlaps = []
        if input_data.comparison_entities:
            for comp_entity in input_data.comparison_entities:
                overlaps.append(
                    {
                        "comparison_entity": comp_entity,
                        "overlap_index": 0.68,
                        "affinity_score": 1.42,
                        "shared_visitors": 5200,
                    }
                )

        return {
            "profiles": profiles,
            "overlaps": overlaps if input_data.comparison_entities else None,
            "time_range": input_data.time_range,
        }


class GetVisitFlowsTool:
    """Analyze before/after visit patterns and customer journeys"""

    name = "get_visit_flows"
    description = """Get visit flow patterns showing where visitors go before/after visiting a location.

    Returns:
    - Cross-shopping patterns
    - Journey sequences
    - Dwell time at destinations
    - Co-visitation frequencies

    Use for understanding customer journeys and cross-shopping behavior."""

    def get_input_schema(self) -> dict:
        return GetVisitFlowsInput.model_json_schema()

    async def execute(self, **kwargs: Any) -> dict:
        try:
            input_data = GetVisitFlowsInput(**kwargs)
        except Exception as e:
            return {
                "error": f"Invalid input parameters: {str(e)}",
                "flows": [],
            }

        # Mock journey flow data
        flows = []
        for origin_id in input_data.origin_place_ids:
            flows.append(
                {
                    "origin_place_id": origin_id,
                    "before_visit_destinations": [
                        {
                            "destination_name": "Whole Foods Market",
                            "destination_id": "place_wf_001",
                            "shared_visitors": 2800,
                            "avg_time_before_minutes": 45,
                        },
                        {
                            "destination_name": "Target",
                            "destination_id": "place_tgt_001",
                            "shared_visitors": 2200,
                            "avg_time_before_minutes": 65,
                        },
                    ],
                    "after_visit_destinations": [
                        {
                            "destination_name": "Starbucks",
                            "destination_id": "place_sbux_001",
                            "shared_visitors": 3500,
                            "avg_time_after_minutes": 15,
                        },
                        {
                            "destination_name": "Trader Joe's",
                            "destination_id": "place_tj_001",
                            "shared_visitors": 1800,
                            "avg_time_after_minutes": 30,
                        },
                    ],
                }
            )

        return {
            "flows": flows,
            "time_range": input_data.time_range,
            "window_config": {
                "before_minutes": input_data.window_before_minutes,
                "after_minutes": input_data.window_after_minutes,
            },
        }


# ============================================================================
# Tool Registry Export
# ============================================================================

PLACER_TOOLS = [
    SearchPlacesTool(),
    GetPlaceSummaryTool(),
    CompareLocationsTool(),
    GetTradeAreaProfileTool(),
    GetProfileAndOverlapTool(),
    GetVisitFlowsTool(),
]
