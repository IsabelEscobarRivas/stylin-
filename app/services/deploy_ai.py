"""
deploy_ai.py — Reusable DeployAI API client.

Handles:
- OAuth2 client_credentials token fetch with in-memory TTL cache
- Chat session creation
- Message dispatch (text + image content types)
- Auto-token refresh on 401

Used by both Vision Scout and Style Curator agents.
"""

import time
from typing import Any, Dict, List, Optional
import requests

from app.config import settings
from app.utils.logger import get_logger

logger = get_logger("stylin.deploy_ai")


class TokenCache:
    """Simple in-memory token cache with TTL."""

    def __init__(self):
        self._token: Optional[str] = None
        self._expires_at: float = 0.0

    def get(self) -> Optional[str]:
        if self._token and time.time() < self._expires_at:
            return self._token
        return None

    def set(self, token: str, ttl: int = settings.token_cache_ttl) -> None:
        self._token = token
        self._expires_at = time.time() + ttl


_token_cache = TokenCache()


class DeployAIClient:
    """
    Thin wrapper around DeployAI REST API.
    All methods are synchronous (requests); async version can be added via httpx.
    """

    def __init__(self):
        self.api_url = settings.api_url
        self.auth_url = settings.auth_url

    # ── Auth ──────────────────────────────────────────────────────────────────

    def _get_access_token(self) -> str:
        """Fetch a new OAuth2 token or return the cached one."""
        cached = _token_cache.get()
        if cached:
            logger.debug("Using cached DeployAI access token")
            return cached

        logger.info("Fetching new DeployAI access token")
        response = requests.post(
            self.auth_url,
            data={
                "grant_type": "client_credentials",
                "client_id": settings.client_id,
                "client_secret": settings.client_secret,
            },
            timeout=10,
        )
        response.raise_for_status()
        token = response.json()["access_token"]
        _token_cache.set(token)
        logger.info("DeployAI access token refreshed successfully")
        return token

    def _headers(self, token: str) -> Dict[str, str]:
        return {
            "accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"Bearer {token}",
            "X-Org": settings.org_id,
        }

    # ── Chat Management ───────────────────────────────────────────────────────

    def create_chat(self, agent_id: str) -> str:
        """
        Create a new chat session for a given agent.
        Returns the chat_id string.
        """
        token = self._get_access_token()
        payload = {
            "agentId": agent_id,
            "stream": False,
        }
        logger.info("Creating DeployAI chat", extra={"agent_id": agent_id})
        response = requests.post(
            f"{self.api_url}/chats",
            headers=self._headers(token),
            json=payload,
            timeout=15,
        )

        if response.status_code == 401:
            # Token expired mid-session — force refresh once
            logger.warning("Token expired during chat creation, refreshing")
            _token_cache._token = None
            token = self._get_access_token()
            response = requests.post(
                f"{self.api_url}/chats",
                headers=self._headers(token),
                json=payload,
                timeout=15,
            )

        response.raise_for_status()
        chat_id = response.json()["id"]
        logger.info("Chat session created", extra={"chat_id": chat_id, "agent_id": agent_id})
        return chat_id

    # ── Messaging ─────────────────────────────────────────────────────────────

    def send_message(
        self,
        chat_id: str,
        content: List[Dict[str, Any]],
    ) -> str:
        """
        Send a message to an existing chat session.

        content: list of content blocks, e.g.
          [{"type": "text", "value": "Analyze this image..."},
           {"type": "image_url", "value": "https://..."}]

        Returns the first text value from the response content.
        """
        token = self._get_access_token()
        payload = {
            "chatId": chat_id,
            "stream": False,
            "content": content,
        }
        logger.debug("Sending message to DeployAI", extra={"chat_id": chat_id})
        response = requests.post(
            f"{self.api_url}/messages",
            headers=self._headers(token),
            json=payload,
            timeout=30,  # Vision analysis can take up to ~10s
        )

        if response.status_code == 401:
            logger.warning("Token expired during message send, refreshing")
            _token_cache._token = None
            token = self._get_access_token()
            response = requests.post(
                f"{self.api_url}/messages",
                headers=self._headers(token),
                json=payload,
                timeout=30,
            )

        response.raise_for_status()
        result = response.json()
        # Extract first text content block
        content_blocks = result.get("content", [])
        for block in content_blocks:
            if block.get("type") == "text":
                return block["value"]
        # Fallback: return raw response text
        return str(result)

    # ── Convenience: one-shot call ────────────────────────────────────────────

    def query(
        self,
        agent_id: str,
        content: List[Dict[str, Any]],
    ) -> str:
        """
        One-shot: create chat → send message → return response.
        Use for stateless agent calls (Vision Scout, Style Curator).
        """
        chat_id = self.create_chat(agent_id)
        return self.send_message(chat_id, content)


# Singleton client — import and reuse across agents
deploy_ai_client = DeployAIClient()
