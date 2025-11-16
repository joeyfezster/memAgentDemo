from __future__ import annotations

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationInfo, field_validator


class TimeRange(BaseModel):
    start: date
    end: date

    @field_validator("end")
    @classmethod
    def validate_range(cls, value: date, info: ValidationInfo) -> date:
        start = info.data.get("start") if info is not None else None
        if start and value < start:
            raise ValueError("end must be on or after start")
        return value


class EntityReference(BaseModel):
    type: Literal["place", "chain"]
    id: str


class GeoFilter(BaseModel):
    type: Literal["point_radius", "bounding_box", "metro", "polygon"]
    config: dict


class ToolResult(BaseModel):
    status: Literal["ok"] = "ok"

    def as_dict(self) -> dict:
        data = self.model_dump()
        return data


class SearchPlacesInput(BaseModel):
    geo_filter: Optional[GeoFilter] = None
    category_ids: Optional[list[str]] = None
    chain_ids: Optional[list[str]] = None
    text_query: Optional[str] = None
    portfolio_tags: Optional[list[str]] = None
    min_visits: Optional[int] = None
    limit: Optional[int] = Field(default=10, ge=1, le=50)


class PlaceSummaryInput(BaseModel):
    place_ids: list[str]
    time_range: TimeRange
    granularity: Literal["daily", "weekly", "monthly"] = "monthly"
    include_benchmark: bool = True
    include_rollup: bool = False


class AudienceProfileInput(BaseModel):
    base_entities: list[EntityReference]
    comparison_entities: Optional[list[EntityReference]] = None
    baseline: Optional[dict] = None
    time_range: TimeRange
    dimensions: Optional[list[str]] = None


class JourneyInput(BaseModel):
    origin_place_ids: list[str]
    time_range: TimeRange
    window_before_minutes: int = 120
    window_after_minutes: int = 240
    group_by: Literal["destination_place", "destination_chain", "destination_category"] = (
        "destination_place"
    )
    min_shared_visitors: int = 0


class PerformanceInput(BaseModel):
    entities: list[EntityReference]
    time_range: TimeRange
    metric: Literal["visits", "visit_frequency", "dwell_time"] = "visits"
    benchmark: Optional[dict] = None
    classification_thresholds: Optional[dict] = None


class TradeAreaInput(BaseModel):
    place_ids: list[str]
    time_range: TimeRange
    output_geography: Literal["block_group", "census_tract", "zip", "cbg"] = "zip"
    include_demographics: bool = True
    include_psychographics: bool = True
    max_radius_km: Optional[float] = None
