"""Deterministic natural-language query parsing for satellite retrieval."""

import re
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RetrievalQuery:
    """Structured constraints extracted from a user retrieval query."""

    original_query: str
    semantic_query: str
    date_preference: Optional[str] = None
    temporal_preference: Optional[str] = None
    land_use: Optional[str] = None
    change_type: Optional[str] = None
    near_features: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


class QueryParser:
    """Parse common remote-sensing intents without an LLM dependency."""

    _LAND_USE_TERMS = {
        "construction": ("construction", "new construction", "building", "buildings"),
        "industrial": ("industrial", "industry", "factory", "factories"),
        "vegetation": ("vegetation", "forest", "green space", "cropland"),
        "water": ("water", "water body", "waterbody", "lake", "lakes", "river"),
        "settlement": ("settlement", "urban", "residential", "dense settlements"),
        "infrastructure": ("infrastructure", "development"),
    }
    _CHANGE_TERMS = {
        "new_construction": ("new construction", "newly developed", "construction increased"),
        "building_expansion": ("building expansion", "building growth", "expanded buildings"),
        "vegetation_loss": ("vegetation loss", "vegetation cleared", "deforestation", "forest loss"),
        "water_body_change": ("water-body change", "water body change", "water level change"),
        "road_development": ("road development", "new roads", "road expansion"),
        "land_use_change": ("land-use change", "land use change"),
        "disturbed_area": ("disturbed area", "cleared area", "cleared land"),
    }
    _FEATURE_TERMS = {
        "roads": ("near roads", "near major roads", "road", "roads", "highway"),
        "rivers": ("near rivers", "river"),
        "lakes": ("near lakes", "lake"),
        "settlements": ("near settlements", "near dense settlements", "settlements"),
    }

    def parse(self, query: str) -> RetrievalQuery:
        normalized = " ".join(query.strip().lower().split())
        if not normalized:
            raise ValueError("Retrieval query cannot be empty")

        land_use = self._first_match(normalized, self._LAND_USE_TERMS)
        change_type = self._first_match(normalized, self._CHANGE_TERMS)
        if change_type is None and land_use == "construction" and "recent" in normalized:
            change_type = "new_construction"
        near_features = self._all_matches(normalized, self._FEATURE_TERMS)
        date_preference = "recent" if self._contains_any(normalized, ("recent", "latest", "newest")) else None
        temporal_preference = self._temporal_preference(normalized)

        semantic_query = normalized
        removable_phrases = (
            "show areas with", "show", "find areas with", "find", "areas with", "during the last year"
        )
        for phrase in removable_phrases:
            semantic_query = semantic_query.replace(phrase, " ")
        semantic_query = " ".join(semantic_query.split())
        if not semantic_query:
            semantic_query = normalized

        return RetrievalQuery(
            original_query=query,
            semantic_query=semantic_query,
            date_preference=date_preference,
            temporal_preference=temporal_preference,
            land_use=land_use,
            change_type=change_type,
            near_features=near_features,
        )

    @staticmethod
    def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
        return any(term in text for term in terms)

    @classmethod
    def _first_match(cls, text: str, groups: Dict[str, tuple[str, ...]]) -> Optional[str]:
        matches = [(key, max((len(term) for term in terms if term in text), default=0)) for key, terms in groups.items()]
        matches = [item for item in matches if item[1] > 0]
        return max(matches, key=lambda item: item[1])[0] if matches else None

    @classmethod
    def _all_matches(cls, text: str, groups: Dict[str, tuple[str, ...]]) -> List[str]:
        return [key for key, terms in groups.items() if any(term in text for term in terms)]

    @staticmethod
    def _temporal_preference(text: str) -> Optional[str]:
        if re.search(r"last\s+(year|12\s+months)", text):
            return "last_year"
        if "last month" in text:
            return "last_month"
        if "over time" in text or "multi temporal" in text or "multi-temporal" in text:
            return "multi_date"
        return None


def parse_query(query: str) -> RetrievalQuery:
    """Convenience function for callers that do not need a parser instance."""

    return QueryParser().parse(query)