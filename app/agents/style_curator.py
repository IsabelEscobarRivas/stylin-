"""
style_curator.py — Agent 2: Style Curator

Responsibility:
  Receives a StyleProfile from Vision Scout, dispatches it to Claude via
  Anthropic's messages API, and returns a validated CurationResult containing:
    - A named style persona
    - 3 matched products across budget / mid-range / luxury price tiers
    - 3 complete, shoppable outfit recommendations

Pipeline position:
  StyleProfile → [Style Curator] → CurationResult

Latency target: ≤ 10s (per PRD p95 requirement)

Note (v1 scaffold):
  Product matching uses Claude's knowledge base as a realistic placeholder.
  In production, this layer will fan out to real retailer APIs (ASOS, Google
  Shopping, Rakuten affiliate network) and Claude will rank + assemble.
"""

import json
import re

from app.config import settings
from app.models.style_profile import StyleProfile
from app.models.curation_result import CurationResult
from app.services.anthropic_client import anthropic_client
from app.utils.logger import get_logger

logger = get_logger("stylin.style_curator")

# ── System prompt ─────────────────────────────────────────────────────────────
CURATOR_SYSTEM = """You are Style Curator, the personal stylist AI for the Stylin' app.
Your personality is warm, confident, and inclusive — like a cool friend who always knows what to wear.
You speak plainly, not in luxury-magazine jargon. You celebrate all budgets equally.
You return only structured JSON. Never hallucinate URLs — use placeholder paths like 'https://asos.com/product/placeholder-id'."""

CURATOR_USER_TEMPLATE = """A user just uploaded a fashion photo. Vision Scout analyzed it and produced this StyleProfile:

{style_profile_json}

Your job: build a complete CurationResult JSON. This includes:

1. STYLE PERSONA — assign a named persona that captures this person's aesthetic soul.
   Examples: "The Romantic Minimalist", "The Elevated Streetwear Kid", "The Conscious Classic"

2. MATCHED PRODUCTS — find the EXACT item type from the StyleProfile at 3 price points.
   Use DIFFERENT retailers for each tier — never repeat a retailer across tiers.
   - budget: under $80 — choose ONE of: ASOS, H&M, Zara, Target
   - mid-range: $80–$250 — choose ONE of: Free People, Anthropologie, Madewell, & Other Stories
   - luxury: $250+ — choose ONE of: Reformation, Polene, Toteme, Sandro, Jacquemus

3. THREE OUTFITS — build 3 complete, shoppable looks using the identified item as the anchor.
   Each outfit must have:
   - A name that evokes a mood (not just "Outfit 1")
   - 4–6 component items (the anchor piece + complementary items)
   - An occasion, a vibe sentence, and one practical styling tip
   - Realistic price ranges and a retailer_hint for EACH item
   - Use varied retailers for outfit items (Everlane, Madewell, Veja, & Other Stories, COS, Uniqlo, etc.)

RULES:
1. Return ONLY valid JSON — no markdown, no code fences, no commentary
2. All string values lowercase except persona name, brand names, and style icons
3. matched_products must be an array of exactly 3 objects (one per tier)
4. outfits must be an array of exactly 3 objects
5. Use realistic retailer names and realistic prices
6. Product URLs format: "https://<retailer-domain>/product/placeholder"
7. CRITICAL — product "name" field must be a plain descriptive name only.
   GOOD: "cotton midi dress with puff sleeves", "oversized wool coat in camel"
   BAD: "Counting Daisies Dress", "Cloud Nine Coat" — no invented product names ever
8. Every outfit item MUST include a retailer_hint field

Return exactly this structure:
{{
  "style_persona": {{
    "name": "<Persona Name>",
    "tagline": "<one sentence>",
    "defining_traits": ["<trait1>", "<trait2>", "<trait3>"],
    "brands_you_love": ["<brand1>", "<brand2>", "<brand3>"],
    "style_icons": ["<icon1>", "<icon2>"]
  }},
  "matched_products": [
    {{
      "tier": "budget",
      "retailer": "<name>",
      "name": "<product name>",
      "description": "<short description>",
      "price": <number>,
      "url": "<url>",
      "colors": ["<color1>"],
      "image_hint": "<visual description>"
    }},
    {{
      "tier": "mid-range",
      "retailer": "<name>",
      "name": "<product name>",
      "description": "<short description>",
      "price": <number>,
      "url": "<url>",
      "colors": ["<color1>"],
      "image_hint": "<visual description>"
    }},
    {{
      "tier": "luxury",
      "retailer": "<name>",
      "name": "<product name>",
      "description": "<short description>",
      "price": <number>,
      "url": "<url>",
      "colors": ["<color1>"],
      "image_hint": "<visual description>"
    }}
  ],
  "outfits": [
    {{
      "id": 1,
      "name": "<outfit name>",
      "occasion": "<occasion>",
      "vibe": "<one-line vibe>",
      "items": [
        {{
          "category": "<category>",
          "name": "<item name>",
          "color": "<color>",
          "style_note": "<why it works>",
          "retailer_hint": "<retailer>",
          "price_range": "<$XX–$XX>"
        }}
      ],
      "styling_tip": "<one practical tip>"
    }},
    {{
      "id": 2,
      "name": "<outfit name>",
      "occasion": "<occasion>",
      "vibe": "<one-line vibe>",
      "items": [...],
      "styling_tip": "<one practical tip>"
    }},
    {{
      "id": 3,
      "name": "<outfit name>",
      "occasion": "<occasion>",
      "vibe": "<one-line vibe>",
      "items": [...],
      "styling_tip": "<one practical tip>"
    }}
  ],
  "curator_notes": "<optional 1–2 sentence style direction note>"
}}"""


class StyleCurator:
    """
    Style Curator agent — StyleProfile → CurationResult.

    Takes the structured output of Vision Scout and builds:
    - A named style persona
    - 3 matched products (one per price tier)
    - 3 complete outfit recommendations
    """

    def curate(self, style_profile: StyleProfile) -> CurationResult:
        """
        Main entry point. Accepts a validated StyleProfile and returns
        a fully populated CurationResult.
        """
        logger.info(
            "Style Curator: starting curation",
            extra={
                "item_type": style_profile.item_type,
                "price_tiers": style_profile.price_tier,
                "occasion": style_profile.occasion,
            }
        )

        # Serialize StyleProfile to JSON for the prompt
        profile_json = style_profile.model_dump_json(indent=2)
        user_prompt = CURATOR_USER_TEMPLATE.format(style_profile_json=profile_json)

        try:
            raw = anthropic_client.call(
                content=[anthropic_client.text_block(user_prompt)],
                system=CURATOR_SYSTEM,
                max_tokens=settings.curator_max_tokens,
            )
            logger.debug(
                "Style Curator raw response",
                extra={"preview": raw[:300]}
            )
        except Exception as e:
            logger.error(
                "Anthropic call failed in Style Curator",
                extra={"error": str(e)},
                exc_info=True,
            )
            raise StyleCuratorError(f"Style curation service unavailable: {e}") from e

        result = self._parse(raw)
        logger.info(
            "Style Curator complete",
            extra={
                "persona": result.style_persona.name,
                "outfit_count": len(result.outfits),
                "product_count": len(result.matched_products),
            }
        )
        return result

    def _parse(self, raw: str) -> CurationResult:
        """Extract JSON from model response and validate as CurationResult."""
        # Strip markdown fences (safety net)
        cleaned = re.sub(r"```(?:json)?\s*", "", raw).strip()
        cleaned = re.sub(r"```\s*$", "", cleaned).strip()

        # Find outermost JSON object
        match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if not match:
            logger.error("No JSON in Style Curator response", extra={"raw": raw[:500]})
            raise StyleCuratorError("Style Curator returned an unparseable response")

        try:
            data = json.loads(match.group(0))
        except json.JSONDecodeError as e:
            logger.error("JSON decode error in curator", extra={"error": str(e), "snippet": raw[:400]})
            raise StyleCuratorError(f"Malformed JSON from Style Curator: {e}") from e

        try:
            return CurationResult(**data)
        except Exception as e:
            logger.error(
                "CurationResult validation failed",
                extra={"error": str(e), "data_keys": list(data.keys())}
            )
            raise StyleCuratorError(f"CurationResult validation error: {e}") from e


class StyleCuratorError(Exception):
    """Raised when Style Curator cannot produce a valid CurationResult."""
    pass


# Module-level singleton
style_curator = StyleCurator()
