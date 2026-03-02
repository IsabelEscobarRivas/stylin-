"""
style_profile.py — Pydantic models for the StyleProfile contract.

StyleProfile is the output of Agent 1 (Vision Scout) and the
input to Agent 2 (Style Curator). Schema mirrors the architecture doc.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class PriceTier(str, Enum):
    BUDGET = "budget"
    MID_RANGE = "mid-range"
    LUXURY = "luxury"


class Season(str, Enum):
    SPRING_SUMMER = "spring/summer"
    FALL_WINTER = "fall/winter"
    ALL_SEASON = "all-season"
    SPRING = "spring"
    SUMMER = "summer"
    FALL = "fall"
    WINTER = "winter"


class StyleProfile(BaseModel):
    """
    Output contract for Vision Scout Agent.
    Fully matches the architecture spec + extensible for v2.
    """

    # Primary item classification
    item_type: str = Field(
        ...,
        description="Primary clothing or accessory item (e.g. 'midi dress', 'oversized blazer')",
        examples=["midi dress", "wide-leg trousers", "leather jacket"]
    )

    # Color palette
    colors: List[str] = Field(
        ...,
        min_length=1,
        description="Dominant colors detected in the image",
        examples=[["sage green", "cream"], ["navy", "white"]]
    )

    # Style taxonomy
    style_tags: List[str] = Field(
        ...,
        min_length=1,
        description="Style descriptors / aesthetic tags",
        examples=[["cottagecore", "romantic", "casual"]]
    )

    # Use-case occasions
    occasion: List[str] = Field(
        ...,
        min_length=1,
        description="Occasions the outfit is suitable for",
        examples=[["brunch", "garden party"]]
    )

    # Price positioning
    price_tier: List[PriceTier] = Field(
        ...,
        min_length=1,
        description="Inferred price tier(s) from item quality/branding signals"
    )

    # Seasonality
    season: str = Field(
        ...,
        description="Primary season(s) for the item",
        examples=["spring/summer", "fall/winter", "all-season"]
    )

    # Agent confidence
    confidence_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Vision Scout's confidence in the analysis (0.0–1.0)"
    )

    # Optional metadata
    gender_expression: Optional[str] = Field(
        default=None,
        description="Inferred gender expression (e.g. 'feminine', 'masculine', 'androgynous')"
    )
    pattern: Optional[str] = Field(
        default=None,
        description="Fabric pattern if identifiable (e.g. 'floral', 'plaid', 'solid')"
    )
    fabric_hint: Optional[str] = Field(
        default=None,
        description="Fabric texture hint if visible (e.g. 'linen', 'silk', 'denim')"
    )

    @field_validator("confidence_score")
    @classmethod
    def round_confidence(cls, v: float) -> float:
        return round(v, 4)

    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "item_type": "midi dress",
                "colors": ["sage green", "cream"],
                "style_tags": ["cottagecore", "romantic", "casual"],
                "occasion": ["brunch", "garden party"],
                "price_tier": ["budget", "mid-range", "luxury"],
                "season": "spring/summer",
                "confidence_score": 0.94,
                "gender_expression": "feminine",
                "pattern": "floral",
                "fabric_hint": "cotton"
            }
        }
