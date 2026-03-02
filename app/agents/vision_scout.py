"""
vision_scout.py — Agent 1: Vision Scout

Responsibility:
  Receives a fashion image (URL or bytes), dispatches it to Claude via
  Anthropic's messages API (vision), parses the structured JSON response,
  and returns a validated StyleProfile Pydantic model.

Pipeline position:
  Image → [Vision Scout] → StyleProfile → Style Curator

Latency target: ≤ 5s (per PRD p95 requirement)
"""

import json
import re
import base64
from typing import Optional

from app.config import settings
from app.models.style_profile import StyleProfile
from app.services.anthropic_client import anthropic_client
from app.utils.logger import get_logger

logger = get_logger("stylin.vision_scout")

# ── System prompt ─────────────────────────────────────────────────────────────
VISION_SCOUT_SYSTEM = """You are Vision Scout, an expert AI fashion analyst for the Stylin' app.
Your sole job is to analyze fashion images and return precise, structured JSON.
You are thorough, accurate, and never hallucinate brand names or prices.
If you are uncertain, reflect that in a lower confidence_score."""

VISION_SCOUT_USER = """Analyze this fashion image and return a StyleProfile JSON.

Identify carefully:
- The PRIMARY clothing or accessory item (most prominent piece)
- Color palette using descriptive names (e.g. "sage green", "dusty rose", not just "green")
- Style aesthetic tags (e.g. "cottagecore", "old money", "streetwear", "Y2K", "minimalist")
- Occasion suitability (e.g. "brunch", "office", "festival", "black tie", "casual weekend")
- Price tier inference from visible quality/branding/fabric signals
- Season appropriateness
- Optional: gender expression, fabric texture, pattern

STRICT RULES:
1. Return ONLY valid JSON — no markdown fences, no explanation, no preamble
2. All string values lowercase (except proper nouns)
3. price_tier: array with one or more of: "budget", "mid-range", "luxury"
4. confidence_score: 0.0–1.0 (below 0.5 if image is unclear)
5. null values must be JSON null, not the string "null"

Return exactly this structure:
{
  "item_type": "<primary item>",
  "colors": ["<color1>", "<color2>"],
  "style_tags": ["<tag1>", "<tag2>", "<tag3>"],
  "occasion": ["<occasion1>", "<occasion2>"],
  "price_tier": ["<tier>"],
  "season": "<season>",
  "confidence_score": <float>,
  "gender_expression": "<expression>" or null,
  "pattern": "<pattern>" or null,
  "fabric_hint": "<fabric>" or null
}"""


class VisionScout:
    """
    Vision Scout agent — image analysis → StyleProfile.

    Input modes:
    - analyze_from_url(url):          public image URL (fastest)
    - analyze_from_bytes(bytes, mime): multipart file upload
    """

    def analyze_from_url(self, image_url: str) -> StyleProfile:
        """Analyze a fashion image from a public URL."""
        logger.info("Vision Scout: analyzing URL", extra={"image_url": image_url})

        content = [
            anthropic_client.image_url_block(image_url),
            anthropic_client.text_block(VISION_SCOUT_USER),
        ]
        return self._run(content, source="url")

    def analyze_from_bytes(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
    ) -> StyleProfile:
        """Analyze a fashion image from raw bytes (file upload)."""
        logger.info(
            "Vision Scout: analyzing upload",
            extra={"mime_type": mime_type, "size_bytes": len(image_bytes)}
        )
        content = [
            anthropic_client.image_base64_block(image_bytes, media_type=mime_type),
            anthropic_client.text_block(VISION_SCOUT_USER),
        ]
        return self._run(content, source="upload")

    def _run(self, content: list, source: str) -> StyleProfile:
        """Dispatch to Anthropic, parse response, return validated StyleProfile."""
        try:
            raw = anthropic_client.call(
                content=content,
                system=VISION_SCOUT_SYSTEM,
                max_tokens=settings.vision_max_tokens,
            )
            logger.debug(
                "Vision Scout raw response",
                extra={"source": source, "preview": raw[:200]}
            )
        except Exception as e:
            logger.error(
                "Anthropic call failed in Vision Scout",
                extra={"source": source, "error": str(e)},
                exc_info=True,
            )
            raise VisionScoutError(f"Vision analysis service unavailable: {e}") from e

        profile = self._parse(raw)
        logger.info(
            "Vision Scout complete",
            extra={
                "item_type": profile.item_type,
                "confidence": profile.confidence_score,
                "source": source,
            }
        )
        return profile

    def _parse(self, raw: str) -> StyleProfile:
        """Extract JSON from model response and validate as StyleProfile."""
        # Strip any accidental markdown fences
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()

        # Find the outermost JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error("No JSON in Vision Scout response", extra={"raw": raw[:500]})
            raise VisionScoutError("Vision Scout returned an unparseable response")

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            logger.error("JSON decode error", extra={"error": str(e), "snippet": raw[:300]})
            raise VisionScoutError(f"Malformed JSON from Vision Scout: {e}") from e

        # Normalize null-like strings → Python None
        for key in ("gender_expression", "pattern", "fabric_hint"):
            if data.get(key) in ("null", "none", "N/A", "n/a", ""):
                data[key] = None

        try:
            return StyleProfile(**data)
        except Exception as e:
            logger.error("StyleProfile validation failed", extra={"error": str(e), "data": data})
            raise VisionScoutError(f"StyleProfile validation error: {e}") from e


class VisionScoutError(Exception):
    """Raised when Vision Scout cannot produce a valid StyleProfile."""
    pass


# Module-level singleton
vision_scout = VisionScout()
