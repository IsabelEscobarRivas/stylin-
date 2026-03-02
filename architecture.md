# Stylin' — System Architecture

**Version:** 1.0 | **Date:** 2026-03-02 | **Status:** Active

---

## 1. Overview

Stylin' is a **multi-agent AI platform** for fashion discovery. It transforms visual inspiration (photos, screenshots, saved looks) into actionable, budget-matched product recommendations — in seconds.

The system is built on Deploy AI's agent orchestration infrastructure, using two specialized AI agents that communicate through a shared context layer.

---

## 2. High-Level System Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                          CLIENT LAYER                           │
│                   (Web / Mobile / API Consumer)                 │
└──────────────────────────┬──────────────────────────────────────┘
                           │  HTTPS
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                        AUTH LAYER                               │
│          OAuth2 Client Credentials (Deploy AI Auth)             │
│         https://api-auth.dev.deploy.ai/oauth2/token             │
└──────────────────────────┬──────────────────────────────────────┘
                           │  Bearer Token
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                        │
│               Deploy AI Core API (Chat + Messages)              │
│                  https://core-api.dev.deploy.ai                 │
│                                                                 │
│   ┌─────────────────────┐    ┌─────────────────────────────┐   │
│   │    Vision Scout     │───▶│      Style Curator          │   │
│   │  (Image Analysis)   │    │  (Product Recommendations)  │   │
│   └─────────────────────┘    └──────────────┬──────────────┘   │
│                                             │                   │
└─────────────────────────────────────────────┼───────────────────┘
                                              │
                           ┌──────────────────▼──────────────────┐
                           │           DATA LAYER                 │
                           │   StyleProfile (User Style Object)   │
                           └─────────────────────────────────────┘
```

---

## 3. Agent Specifications

### 3.1 Vision Scout

**Role:** Image analysis and style signal extraction

| Attribute | Value |
|---|---|
| Type | AI Agent (Deploy AI) |
| Input | Image (URL or base64), optional text context |
| Output | Style signals: colors, patterns, silhouettes, vibe categories |
| Trigger | User drops a photo or references a visual look |

**Responsibilities:**
- Parse visual input to extract fashion attributes (color palette, garment types, style era, occasion)
- Map extracted signals to internal style taxonomy
- Pass structured style context downstream to Style Curator
- Handle ambiguous or low-quality images gracefully

**Style Signal Schema:**
```json
{
  "dominant_colors": ["#3D2B1F", "#F5E6D3"],
  "garment_types": ["midi dress", "ankle boots"],
  "style_tags": ["cottagecore", "romantic", "neutral"],
  "occasion": "casual-daytime",
  "confidence_score": 0.87
}
```

---

### 3.2 Style Curator

**Role:** Product matching, outfit assembly, and budget tiering

| Attribute | Value |
|---|---|
| Type | AI Agent (Deploy AI) |
| Input | Style signals (from Vision Scout), StyleProfile, budget preference |
| Output | Complete outfit recommendations across 3 budget tiers |
| Trigger | Receives style signals from Vision Scout or direct text input |

**Responsibilities:**
- Match style signals to available products across retailers
- Assemble complete outfits (not just individual items)
- Deliver every recommendation at 3 tiers: Budget / Mid-range / Splurge
- Respect StyleProfile preferences (saved items, disliked styles, size data)
- Surface style persona assignment or update

**Recommendation Schema:**
```json
{
  "style_persona": "The Romantic Minimalist",
  "tiers": {
    "budget": {
      "items": [...],
      "total_price": 89.00
    },
    "mid": {
      "items": [...],
      "total_price": 245.00
    },
    "splurge": {
      "items": [...],
      "total_price": 620.00
    }
  }
}
```

---

## 4. Data Model

### StyleProfile

The central user data object. Persists across sessions and powers personalization.

```python
@dataclass
class StyleProfile:
    user_id: str
    style_persona: str              # e.g., "The Romantic Minimalist"
    preferred_colors: list[str]
    disliked_styles: list[str]
    size_data: dict                 # {"top": "M", "bottom": "28", "shoe": "8"}
    saved_items: list[str]         # Product IDs
    budget_preference: str         # "budget" | "mid" | "splurge" | "all"
    interaction_history: list[dict]
    created_at: datetime
    updated_at: datetime
```

---

## 5. API Communication Layer

### Authentication Flow

```
Client → POST /oauth2/token (client_credentials)
       ← { access_token, expires_in }

Client → POST /chats { agentId, stream: false }
       ← { id: chat_id }

Client → POST /messages { chatId, content: [{ type, value }] }
       ← { content: [{ type, value }] }
```

### Agent Selection (agentId)

| Agent | agentId |
|---|---|
| Vision Scout | Configured in Deploy AI dashboard |
| Style Curator | Configured in Deploy AI dashboard |
| General / Fallback | GPT_4O (default) |

### Chat Continuity

To maintain conversation context within a session, reuse the same `chat_id`:

```python
# Initial message
response = calling_agent(token, chat_id, "Analyze this image: [url]")

# Follow-up in same conversation
response = calling_agent(token, chat_id, "Now find me the budget version of that look")
```

---

## 6. Request / Response Lifecycle

```
1. User uploads photo
         │
2. Vision Scout receives image
   └─ Extracts style signals
   └─ Returns structured signal object
         │
3. Style Curator receives signals + StyleProfile
   └─ Queries product database
   └─ Assembles 3-tier outfit recommendations
   └─ Updates StyleProfile with new interaction
         │
4. Response formatted and returned to user
   └─ 3 complete looks (budget / mid / splurge)
   └─ Style Persona assigned or updated
   └─ Product links with pricing
```

---

## 7. Error Handling Strategy

| Scenario | Handling |
|---|---|
| Auth token expired | Refresh token automatically; retry once |
| Image unreadable | Return friendly fallback + request new image |
| No product matches | Return closest alternatives; log signal miss |
| Agent timeout | Retry with exponential backoff (max 3 attempts) |
| API 5xx | Log error in JSON format; surface user-friendly message |

---

## 8. Logging

All runtime logs are written to `logs/` in JSON format:

```json
{
  "timestamp": "2026-03-02T13:33:47Z",
  "level": "INFO",
  "agent": "vision_scout",
  "event": "image_analyzed",
  "user_id": "usr_abc123",
  "confidence_score": 0.87,
  "duration_ms": 412
}
```

Log levels used: `DEBUG`, `INFO`, `WARNING`, `ERROR`

---

## 9. Security Considerations

- All credentials loaded from environment variables — never hardcoded
- OAuth2 tokens scoped per session, not stored persistently
- User StyleProfile data treated as PII — access controlled at API layer
- No sensitive data logged (tokens, credentials, PII fields)
- HTTPS enforced on all external calls

---

## 10. Scalability Notes

- Agents are stateless by design — scalable horizontally
- StyleProfile persistence layer should be swapped from in-memory to a managed DB (e.g., PostgreSQL, DynamoDB) for production
- Chat session pooling recommended for high-traffic scenarios
- Image processing can be parallelized for batch analysis

---

*Owner: architect | References: Brand Voice Profile, Deploy AI documentation*
