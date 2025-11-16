from __future__ import annotations

from letta_client.client import BaseTool

from . import datasets
from .schemas import AudienceProfileInput
from .utils import audience_similarity, resolve_baseline, shared_visitor_pct


def distribution_index(profile: dict[str, float], baseline: dict[str, float]) -> dict[str, float]:
    indexed = {}
    for key, value in profile.items():
        baseline_value = baseline.get(key, 0.0001)
        indexed[key] = round((value / baseline_value) * 100, 1)
    return indexed


class AudienceProfileTool(BaseTool):
    name: str = "audience.get_profile_and_overlap"
    description: str = "Describe visitor demographics for base entities and compare overlaps."
    args_schema: type[AudienceProfileInput] = AudienceProfileInput

    def run(
        self,
        base_entities: list[dict],
        comparison_entities: list[dict] | None = None,
        baseline: dict | None = None,
        time_range: dict | None = None,
        dimensions: list[str] | None = None,
    ) -> dict:
        resolved_baseline = resolve_baseline(baseline)
        comparison_entities = comparison_entities or []
        base_payload = []
        for entity in base_entities:
            entity_id = entity["id"]
            profile = datasets.AUDIENCE_DATA[entity_id]
            vs_baseline = {
                "age_index": distribution_index(profile["age_distribution"], resolved_baseline["age_distribution"]),
                "income_index": distribution_index(profile["income_distribution"], resolved_baseline["income_distribution"]),
            }
            overlaps = []
            for comparison in comparison_entities:
                comparison_id = comparison["id"]
                comparison_profile = datasets.AUDIENCE_DATA[comparison_id]
                overlaps.append(
                    {
                        "comparison_entity": {
                            "type": comparison["type"],
                            "id": comparison_id,
                            "name": datasets.ENTITY_NAMES[comparison_id],
                        },
                        "audience_similarity_index": audience_similarity(profile, comparison_profile),
                        "shared_visitor_pct": shared_visitor_pct(entity_id, comparison_id),
                    }
                )
            base_payload.append(
                {
                    "entity": {
                        "type": entity["type"],
                        "id": entity_id,
                        "name": datasets.ENTITY_NAMES[entity_id],
                    },
                    "profile": profile,
                    "vs_baseline": vs_baseline,
                    "overlaps": overlaps,
                }
            )
        return {"status": "ok", "results": base_payload}
