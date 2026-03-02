"""
anthropic_client.py — Shared Anthropic API client for Stylin' agents.

Provides a thin, reusable wrapper around the Anthropic Python SDK.
Supports:
  - Text-only messages (Style Curator)
  - Vision messages with image URL (Vision Scout, URL mode)
  - Vision messages with base64 image (Vision Scout, upload mode)

Both Vision Scout and Style Curator import the singleton `anthropic_client`.
"""

import base64
from typing import Any, Dict, List, Literal, Optional

import anthropic

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("stylin.anthropic_client")

# Accepted image MIME types for base64 encoding
ImageMediaType = Literal["image/jpeg", "image/png", "image/gif", "image/webp"]


class AnthropicClient:
    """
    Wrapper around anthropic.Anthropic providing content-block helpers
    for text and vision calls used by both Stylin' agents.
    """

    def __init__(self):
        self._client = anthropic.Anthropic(api_key=settings.anthropic_api_key)
        logger.info(
            "AnthropicClient initialized",
            extra={"model": settings.anthropic_model}
        )

    # ── Content block builders ────────────────────────────────────────────────

    @staticmethod
    def text_block(text: str) -> Dict[str, Any]:
        """Build a plain text content block."""
        return {"type": "text", "text": text}

    @staticmethod
    def image_url_block(url: str) -> Dict[str, Any]:
        """
        Build an image content block from a public URL.
        Anthropic supports direct URL references for images.
        """
        return {
            "type": "image",
            "source": {
                "type": "url",
                "url": url,
            },
        }

    @staticmethod
    def image_base64_block(
        image_bytes: bytes,
        media_type: ImageMediaType = "image/jpeg",
    ) -> Dict[str, Any]:
        """
        Build an image content block from raw bytes (base64 encoded).
        Used for multipart file uploads.
        """
        b64_data = base64.standard_b64encode(image_bytes).decode("utf-8")
        return {
            "type": "image",
            "source": {
                "type": "base64",
                "media_type": media_type,
                "data": b64_data,
            },
        }

    # ── Message dispatch ──────────────────────────────────────────────────────

    def call(
        self,
        content: List[Dict[str, Any]],
        system: Optional[str] = None,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Send a single user message to the Anthropic API and return the
        first text block from the response.

        Args:
            content:    List of content blocks (text and/or image).
            system:     Optional system prompt string.
            max_tokens: Override default max_tokens from settings.

        Returns:
            The model's text response as a plain string.
        """
        tokens = max_tokens or settings.vision_max_tokens

        kwargs: Dict[str, Any] = {
            "model": settings.anthropic_model,
            "max_tokens": tokens,
            "messages": [{"role": "user", "content": content}],
        }
        if system:
            kwargs["system"] = system

        logger.debug(
            "Calling Anthropic API",
            extra={"model": settings.anthropic_model, "max_tokens": tokens, "blocks": len(content)}
        )

        response = self._client.messages.create(**kwargs)

        # Extract first text block
        for block in response.content:
            if block.type == "text":
                logger.debug(
                    "Anthropic API response received",
                    extra={"stop_reason": response.stop_reason, "preview": block.text[:100]}
                )
                return block.text

        raise RuntimeError("Anthropic returned no text content in response")


# Singleton — both agents import this
anthropic_client = AnthropicClient()
