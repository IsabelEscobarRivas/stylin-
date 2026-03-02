"""
requests.py — FastAPI request/response envelope models for /analyze and /curate endpoints.
"""

from typing import Optional
from pydantic import BaseModel, Field
from .style_profile import StyleProfile
from .curation_result import CurationResult


class AnalyzeURLRequest(BaseModel):
    """Body for JSON-based analyze requests (pass a public image URL)."""
    image_url: str = Field(
        ...,
        description="Publicly accessible URL of the fashion image to analyze"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional authenticated user ID for profile persistence"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "image_url": "https://example.com/fashion-photo.jpg",
                "user_id": "usr_abc123"
            }
        }


class AnalyzeResponse(BaseModel):
    """Envelope returned by POST /analyze — wraps StyleProfile + metadata."""
    success: bool = Field(..., description="Whether Vision Scout analysis succeeded")
    session_id: str = Field(..., description="Unique ID for this analysis session")
    style_profile: Optional[StyleProfile] = Field(
        default=None,
        description="StyleProfile output from Vision Scout"
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error message if success=False"
    )
    latency_ms: Optional[int] = Field(
        default=None,
        description="End-to-end Vision Scout latency in milliseconds"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "session_id": "sess_20260302_xk9f3",
                "style_profile": {
                    "item_type": "midi dress",
                    "colors": ["sage green", "cream"],
                    "style_tags": ["cottagecore", "romantic", "casual"],
                    "occasion": ["brunch", "garden party"],
                    "price_tier": ["budget", "mid-range"],
                    "season": "spring/summer",
                    "confidence_score": 0.94
                },
                "latency_ms": 3421
            }
        }


class HealthResponse(BaseModel):
    """Response for GET /health."""
    status: str
    version: str
    environment: str


# ── Style Curator (Agent 2) models ────────────────────────────────────────────

class CurateRequest(BaseModel):
    """Body for POST /curate — accepts the StyleProfile from Vision Scout."""
    style_profile: StyleProfile = Field(
        ...,
        description="StyleProfile JSON produced by Vision Scout (POST /analyze)"
    )
    user_id: Optional[str] = Field(
        default=None,
        description="Optional authenticated user ID for persona persistence"
    )

    class Config:
        json_schema_extra = {
            "example": {
                "style_profile": {
                    "item_type": "midi dress",
                    "colors": ["sage green", "cream"],
                    "style_tags": ["cottagecore", "romantic", "casual"],
                    "occasion": ["brunch", "garden party"],
                    "price_tier": ["budget", "mid-range"],
                    "season": "spring/summer",
                    "confidence_score": 0.94
                }
            }
        }


class CurateResponse(BaseModel):
    """Envelope returned by POST /curate — wraps CurationResult + metadata."""
    success: bool = Field(..., description="Whether Style Curator curation succeeded")
    session_id: str = Field(..., description="Session ID (pass from /analyze if chaining)")
    curation_result: Optional[CurationResult] = Field(
        default=None,
        description="Full CurationResult from Style Curator"
    )
    error: Optional[str] = Field(
        default=None,
        description="Human-readable error message if success=False"
    )
    latency_ms: Optional[int] = Field(
        default=None,
        description="Style Curator latency in milliseconds"
    )
