from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping, Sequence

from app.agents.base import RoutingDecision


@dataclass
class RoutingSignalParser:
    pattern: re.Pattern[str] = re.compile(r"target\s*[:=]\s*(specialized|generalist)", re.IGNORECASE)
    confidence_pattern: re.Pattern[str] = re.compile(r"confidence\s*[:=]\s*(\d+\.?\d*)", re.IGNORECASE)

    def parse(self, payload: str, slug_map: Mapping[str, str]) -> RoutingDecision | None:
        match = self.pattern.search(payload)
        if not match:
            return None
        key = match.group(1).lower()
        target_slug = slug_map.get(key)
        if not target_slug:
            return None
        confidence_match = self.confidence_pattern.search(payload)
        confidence = float(confidence_match.group(1)) if confidence_match else 0.5
        reason = payload.strip()
        return RoutingDecision(target_slug=target_slug, confidence=confidence, reason=reason)


class KeywordRoutingModel:
    def __init__(self, keyword_mapping: Mapping[str, Sequence[str]], default_slug: str):
        self.keyword_mapping = {
            slug: tuple({keyword.lower() for keyword in keywords})
            for slug, keywords in keyword_mapping.items()
        }
        self.default_slug = default_slug

    def decide(self, message: str) -> RoutingDecision:
        normalized = message.lower()
        for slug, keywords in self.keyword_mapping.items():
            for keyword in keywords:
                if keyword and keyword in normalized:
                    score = min(1.0, 0.5 + len(keyword) / 20)
                    return RoutingDecision(
                        target_slug=slug,
                        confidence=score,
                        reason=f"keyword:{keyword}",
                    )
        return RoutingDecision(target_slug=self.default_slug, confidence=0.4, reason="fallback-default")
