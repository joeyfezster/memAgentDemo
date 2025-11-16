from datetime import date

from agent.tools.letta_tools import (
    AudienceProfileArgs,
    AudienceProfileTool,
    EntityReference,
    PlaceInsightsTool,
    PlaceSummaryArgs,
    PlacesSearchArgs,
    PlacesSearchTool,
    PerformanceCompareArgs,
    PerformanceCompareTool,
    TimeRange,
    TradeAreaProfileArgs,
    TradeAreaProfileTool,
    VisitFlowsArgs,
    VisitFlowsTool,
)


def test_places_search_returns_filtered_results():
    tool = PlacesSearchTool()
    args = PlacesSearchArgs(
        geo_filter={"type": "metro", "config": {"name": "nyc"}},
        category_ids=["regional_mall"],
        limit=5,
    )
    result = tool.run(**args.model_dump())
    assert result["places"]
    assert all(place["category_id"] == "regional_mall" for place in result["places"])


def test_place_insights_rollup_and_benchmark():
    tool = PlaceInsightsTool()
    args = PlaceSummaryArgs(
        place_ids=["place_garden_state_plaza", "place_willowbrook_center"],
        time_range=TimeRange(start=date(2024, 1, 1), end=date(2024, 6, 30)),
        include_benchmark=True,
        include_rollup=True,
    )
    result = tool.run(**args.model_dump())
    assert len(result["places"]) == 2
    assert "benchmark" in result["places"][0]
    assert "rollup" in result


def test_performance_compare_creates_rankings():
    tool = PerformanceCompareTool()
    args = PerformanceCompareArgs(
        entities=[
            EntityReference(type="place", id="place_garden_state_plaza"),
            EntityReference(type="place", id="place_willowbrook_center"),
        ],
        time_range=TimeRange(start=date(2024, 1, 1), end=date(2024, 12, 31)),
        metric="visits",
    )
    result = tool.run(**args.model_dump())
    assert len(result["rankings"][0]["ranked_entities"]) == 2
    assert result["series"][0]["classification"] in {"growing", "stable", "declining"}


def test_trade_area_profile_filters_by_radius_and_psychographics():
    tool = TradeAreaProfileTool()
    args = TradeAreaProfileArgs(
        place_ids=["place_paramus_drive_chickfila"],
        time_range=TimeRange(start=date(2024, 1, 1), end=date(2024, 12, 31)),
        max_radius_km=10,
        include_psychographics=True,
    )
    result = tool.run(**args.model_dump())
    units = result["profiles"][0]["geo_units"]
    assert all(unit["avg_distance_km"] <= 10 for unit in units)
    assert any("psychographics_index" in unit for unit in units)


def test_audience_profile_reports_overlap():
    tool = AudienceProfileTool()
    args = AudienceProfileArgs(
        base_entities=[EntityReference(type="place", id="place_eagle_creek_golf")],
        comparison_entities=[EntityReference(type="place", id="place_midtown_quickstop")],
        baseline={"id": "atlanta_metro"},
        time_range=TimeRange(start=date(2024, 1, 1), end=date(2024, 12, 31)),
    )
    result = tool.run(**args.model_dump())
    payload = result["results"][0]
    assert payload["overlaps"][0]["audience_similarity_index"] > 0
    assert "vs_baseline" in payload


def test_visit_flows_aggregates_multiple_origins():
    tool = VisitFlowsTool()
    args = VisitFlowsArgs(
        origin_place_ids=["place_eagle_creek_golf", "place_green_valley_golf"],
        time_range=TimeRange(start=date(2024, 1, 1), end=date(2024, 12, 31)),
        group_by="destination_chain",
        min_shared_visitors=9000,
    )
    result = tool.run(**args.model_dump())
    assert len(result["origins"]) == 2
    assert result["aggregate"]
    assert all(entry["shared_visitors"] >= 9000 for entry in result["aggregate"])
