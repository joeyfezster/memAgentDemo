from __future__ import annotations

from app.agents.routing import KeywordRoutingModel, RoutingSignalParser


def test_keyword_router_prefers_specialized_keywords():
    model = KeywordRoutingModel(
        keyword_mapping={"specialized-analyst": ["analysis", "dataset"]},
        default_slug="generalist-analyst",
    )
    decision = model.decide("Need dataset analysis on churn trends")
    assert decision.target_slug == "specialized-analyst"
    assert decision.reason == "keyword:dataset" or decision.reason == "keyword:analysis"


def test_keyword_router_falls_back_to_generalist():
    model = KeywordRoutingModel(
        keyword_mapping={"specialized-analyst": ["metric"]},
        default_slug="generalist-analyst",
    )
    decision = model.decide("Plan a leadership note")
    assert decision.target_slug == "generalist-analyst"
    assert decision.reason == "fallback-default"


def test_signal_parser_interprets_target_tokens():
    parser = RoutingSignalParser()
    payload = "target=specialized confidence=0.8 reason=metrics"
    mapping = {"specialized": "specialized-analyst", "generalist": "generalist-analyst"}
    decision = parser.parse(payload, mapping)
    assert decision is not None
    assert decision.target_slug == "specialized-analyst"
    assert decision.confidence == 0.8
