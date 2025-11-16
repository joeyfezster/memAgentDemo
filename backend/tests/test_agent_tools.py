from datetime import date

import pytest

from agent.tools import (
    AudienceProfileTool,
    JourneysVisitFlowsTool,
    PerformanceCompareLocationsTool,
    PlaceInsightsTool,
    PlacesSearchTool,
    TradeAreaProfileTool,
    get_all_tools,
)


def sample_range() -> dict:
    return {"start": date(2024, 1, 1), "end": date(2024, 6, 1)}


def test_tool_registry_contains_all_tools():
    tools = get_all_tools()
    assert {tool.name for tool in tools} == {
        "places.search_places",
        "place_insights.get_place_summary",
        "audience.get_profile_and_overlap",
        "journeys.get_visit_flows",
        "performance.compare_locations",
        "trade_area.get_trade_area_profile",
    }


def test_places_search_filters_by_category():
    tool = PlacesSearchTool()
    response = tool.run(
        geo_filter={"type": "metro", "config": {"id": "chicago"}},
        category_ids=["golf_course"],
        limit=5,
    )
    names = [place["name"] for place in response["places"]]
    assert names == ["Summit Ridge Golf Club"]


def test_place_insights_rollup_and_benchmark():
    tool = PlaceInsightsTool()
    result = tool.run(
        place_ids=["plc_northwood_town_center", "plc_freshmart_aurora"],
        time_range=sample_range(),
        include_benchmark=True,
        include_rollup=True,
    )
    assert "rollup" in result
    indices = [place["benchmark"]["index"] for place in result["places"] if place["benchmark"]]
    assert all(index > 50 for index in indices)


def test_audience_tool_reports_overlap_similarity():
    tool = AudienceProfileTool()
    payload = tool.run(
        base_entities=[{"type": "place", "id": "plc_summit_ridge_golf"}],
        comparison_entities=[{"type": "place", "id": "plc_quickmart_lakeview"}],
        baseline={"id": "region_chicago"},
        time_range=sample_range(),
    )
    overlaps = payload["results"][0]["overlaps"]
    assert overlaps[0]["audience_similarity_index"] > 50
    assert overlaps[0]["shared_visitor_pct"] > 0.3


def test_journeys_group_by_category():
    tool = JourneysVisitFlowsTool()
    output = tool.run(
        origin_place_ids=["plc_summit_ridge_golf"],
        time_range=sample_range(),
        group_by="destination_category",
        min_shared_visitors=3000,
    )
    flows = output["results"][0]["flows_out"]
    categories = {flow["destination"]["type"] for flow in flows}
    assert categories == {"category"}


def test_performance_ranking_orders_descending():
    tool = PerformanceCompareLocationsTool()
    response = tool.run(
        entities=[
            {"type": "place", "id": "plc_northwood_town_center"},
            {"type": "place", "id": "plc_riverbend_plaza"},
        ],
        time_range=sample_range(),
        metric="visits",
        benchmark={"type": "category_region"},
    )
    rankings = response["rankings"]
    assert rankings[0]["value"] >= rankings[1]["value"]


def test_trade_area_includes_demographics_controls():
    tool = TradeAreaProfileTool()
    data = tool.run(
        place_ids=["plc_northwood_town_center"],
        time_range=sample_range(),
        include_demographics=False,
        include_psychographics=True,
    )
    geo_unit = data["trade_areas"][0]["geo_units"][0]
    assert "psychographics" in geo_unit
    assert "demographics" not in geo_unit
