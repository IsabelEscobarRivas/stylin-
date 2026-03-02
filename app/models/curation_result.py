"""
curation_result.py — Pydantic models for the CurationResult contract.

CurationResult is the output of Agent 2 (Style Curator).
Schema mirrors the architecture doc exactly, extended with outfit detail.
"""

from typing import List, Optional
from pydantic import BaseModel, Field, HttpUrl

from app.models.style_profile import PriceTier


class MatchedProduct(BaseModel):
    """
    A single product match at a specific price tier.
    Three of these (budget / mid-range / luxury) are returned per analysis.
    """
    tier: PriceTier = Field(..., description="Price tier of this product")
    retailer: str = Field(..., description="Retailer name (e.g. 'ASOS', 'Anthropologie')")
    name: str = Field(..., description="Product name/title")
    description: str = Field(..., description="Short product description")
    price: float = Field(..., ge=0, description="Price in USD")
    url: str = Field(..., description="Product or affiliate URL")
    colors: List[str] = Field(default_factory=list, description="Available colors")
    image_hint: Optional[str] = Field(
        default=None,
        description="Visual description for UI placeholder (used until real product images are integrated)"
    )

    class Config:
        use_enum_values = True


class OutfitItem(BaseModel):
    """A single item within a complete outfit recommendation."""
    category: str = Field(..., description="Clothing category (e.g. 'top', 'shoes', 'bag')")
    name: str = Field(..., description="Item name/description")
    color: str = Field(..., description="Suggested color/finish")
    style_note: str = Field(..., description="Why this item works in the outfit")
    retailer_hint: Optional[str] = Field(
        default=None,
        description="Suggested retailer for this item"
    )
    price_range: Optional[str] = Field(
        default=None,
        description="Estimated price range (e.g. '$20–$60')"
    )


class Outfit(BaseModel):
    """
    A complete, shoppable outfit recommendation.
    Each CurationResult contains exactly 3 outfits.
    """
    id: int = Field(..., ge=1, le=3, description="Outfit number (1, 2, or 3)")
    name: str = Field(..., description="Outfit name (e.g. 'Sunday Brunch')")
    occasion: str = Field(..., description="Primary occasion this outfit suits")
    vibe: str = Field(..., description="One-line style description / vibe")
    items: List[OutfitItem] = Field(..., min_length=3, description="Component items (min 3)")
    styling_tip: str = Field(
        ...,
        description="One practical styling tip for the complete look"
    )


class StylePersona(BaseModel):
    """
    Named style persona assigned to the user based on their StyleProfile.
    Evolves with each session per PRD retention requirement.
    """
    name: str = Field(..., description="Persona name (e.g. 'The Romantic Minimalist')")
    tagline: str = Field(..., description="One-sentence persona description")
    defining_traits: List[str] = Field(
        ...,
        min_length=3,
        description="3–5 defining style traits of this persona"
    )
    brands_you_love: List[str] = Field(
        ...,
        min_length=2,
        description="Representative brands that align with this persona"
    )
    style_icons: List[str] = Field(
        default_factory=list,
        description="Cultural or celebrity style icons that embody this persona"
    )


class CurationResult(BaseModel):
    """
    Output contract for Style Curator Agent.
    Fully matches the architecture spec + extended for v1 hackathon.
    """
    style_persona: StylePersona = Field(
        ...,
        description="Named style persona derived from the StyleProfile"
    )
    matched_products: List[MatchedProduct] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 product matches: one per price tier"
    )
    outfits: List[Outfit] = Field(
        ...,
        min_length=3,
        max_length=3,
        description="Exactly 3 complete outfit recommendations"
    )
    curator_notes: Optional[str] = Field(
        default=None,
        description="Optional Style Curator commentary on the overall style direction"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "style_persona": {
                    "name": "The Romantic Minimalist",
                    "tagline": "You speak in quiet statements — clean lines with a soft soul.",
                    "defining_traits": ["effortless", "feminine", "intentional", "soft"],
                    "brands_you_love": ["COS", "& Other Stories", "Reformation"],
                    "style_icons": ["Sofia Coppola", "Zoe Kravitz"]
                },
                "matched_products": [
                    {
                        "tier": "budget",
                        "retailer": "ASOS",
                        "name": "Floral Midi Slip Dress",
                        "description": "Satin-finish midi slip dress in sage floral print",
                        "price": 38.00,
                        "url": "https://asos.com/placeholder",
                        "colors": ["sage green", "cream"]
                    },
                    {
                        "tier": "mid-range",
                        "retailer": "Anthropologie",
                        "name": "Meadow Midi Dress",
                        "description": "Cotton midi dress with delicate floral embroidery",
                        "price": 148.00,
                        "url": "https://anthropologie.com/placeholder",
                        "colors": ["sage green", "ivory"]
                    },
                    {
                        "tier": "luxury",
                        "retailer": "Reformation",
                        "name": "Vittoria Midi Dress",
                        "description": "Sustainable viscose midi dress, floral sage",
                        "price": 298.00,
                        "url": "https://thereformation.com/placeholder",
                        "colors": ["sage"]
                    }
                ],
                "outfits": [
                    {
                        "id": 1,
                        "name": "Sunday Brunch",
                        "occasion": "brunch",
                        "vibe": "effortlessly pretty without trying too hard",
                        "items": [],
                        "styling_tip": "Add a woven tote and mules to keep it grounded."
                    }
                ]
            }
        }
