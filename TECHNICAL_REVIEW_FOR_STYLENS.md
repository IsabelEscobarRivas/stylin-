# Stylin' Codebase Technical Review
## For Stylens Architecture Planning

**Date:** 2026-05-03  
**Scope:** Full codebase review (no implementation changes)  
**Audience:** Architect (Stylens)  
**Status:** Complete

---

## 1. Core User Flow Analysis

### Current Stylin' Flow (Simple, Linear)

```
User uploads photo
        ↓
Vision Scout (Claude Sonnet)
  • Analyze image via base64 or URL
  • Extract: garment type, colors, style tags, occasion, price tier
  • Return: StyleProfile JSON
        ↓
Style Curator (Claude Sonnet)
  • Receive StyleProfile
  • Generate style persona name
  • Build 3 complete outfits (budget/mid/luxury)
  • Match each to 3 products (one per tier)
  • Return: CurationResult JSON
        ↓
User receives results
  • Persona + traits
  • 3 matched products with prices/links
  • 3 complete outfit recommendations
```

### User Interaction Points

**Upload Phase:**
- Dropzone UI accepts file upload (JPEG/PNG/WebP, max 10MB)
- OR paste public image URL
- Tab toggle between upload/URL modes
- Real-time preview shown in dropzone
- Rate limit: 20 req/min (analysis), 10 req/min (full pipeline)

**Result Phase:**
- Displays style persona name + tagline + traits
- Shows 3-tier product recommendations with real retailer links
- Shows 3 complete outfit mockups with styling tips
- No persistence/save mechanism in current UI

### Response Times (from code)
- Vision Scout target: **≤ 5s** (p95)
- Style Curator target: **≤ 10s** (p95)
- Full pipeline target: **≤ 15s** (p95)
- Actual measured via `latency_ms` in all responses

---

## 2. Agent Structure & Patterns

### Vision Scout Agent

**Input Contract:**
```python
# From vision_scout.py
- image_url: str (public URL) OR
- image_bytes: bytes + mime_type (file upload)
```

**Output Contract:**
```python
# StyleProfile (pydantic model)
{
  "item_type": "midi dress",                      # Primary garment
  "colors": ["sage green", "cream"],              # List of descriptive colors
  "style_tags": ["cottagecore", "romantic"],      # Style taxonomy tags
  "occasion": ["brunch", "garden party"],         # Use case occasions
  "price_tier": ["budget", "mid-range"],          # Inferred price positioning
  "season": "spring/summer",                      # Seasonality
  "confidence_score": 0.94,                       # Agent confidence (0.0-1.0)
  "gender_expression": "feminine",                # Optional
  "pattern": "floral",                            # Optional
  "fabric_hint": "linen"                          # Optional
}
```

**System Prompt Pattern:**
```
"You are Vision Scout, an expert AI fashion analyst..."
+ Strict JSON output rules
+ Field validation (lowercase strings, enum values)
+ Confidence scoring guidance
```

**User Prompt Pattern:**
```
Receives image + structured extraction instructions
Returns ONLY valid JSON (no markdown fences)
Handles ambiguous/low-quality images with lower confidence_score
```

**Key Implementation Details:**
- Uses Anthropic Claude Sonnet (claude-sonnet-4-20250514)
- Regex-based JSON extraction (strips markdown fences)
- Pydantic validation post-parse
- Full exception handling with custom `VisionScoutError`
- Logging includes: source (url/upload), item_type, confidence, latency

---

### Style Curator Agent

**Input Contract:**
```python
# From StyleProfile JSON
{
  "item_type": "midi dress",
  "colors": [...],
  "style_tags": [...],
  "occasion": [...],
  "price_tier": [...],
  "season": "spring/summer",
  "confidence_score": 0.94
}
```

**Output Contract:**
```python
# CurationResult (pydantic model)
{
  "style_persona": {
    "name": "The Romantic Minimalist",
    "tagline": "Clean lines with a soft soul",
    "defining_traits": ["effortless", "feminine", "intentional"],
    "brands_you_love": ["COS", "& Other Stories", "Reformation"],
    "style_icons": ["Sofia Coppola", "Zoe Kravitz"]
  },
  "matched_products": [
    {
      "tier": "budget",
      "retailer": "ASOS",
      "name": "cotton midi dress",
      "description": "...",
      "price": 38.00,
      "url": "https://asos.com/product/placeholder",
      "colors": ["sage green"],
      "image_hint": "<visual description>"
    },
    { "tier": "mid-range", "retailer": "Anthropologie", ... },
    { "tier": "luxury", "retailer": "Reformation", ... }
  ],
  "outfits": [
    {
      "id": 1,
      "name": "Sunday Brunch",
      "occasion": "casual brunch",
      "vibe": "relaxed yet polished",
      "items": [
        {
          "category": "dress",
          "name": "midi dress",
          "color": "sage green",
          "style_note": "This is the anchor piece",
          "retailer_hint": "ASOS",
          "price_range": "$30–$50"
        },
        // 3-5 more items per outfit
      ],
      "styling_tip": "<one practical tip>"
    },
    // 2 more outfits (id: 2, 3)
  ],
  "curator_notes": "Optional style direction"
}
```

**System Prompt Pattern:**
```
"You are Style Curator, the personal stylist AI for Stylin'..."
+ Brand voice: warm, confident, plain-spoken
+ JSON-only output rule
+ Strict retailer rules (different per tier, realistic names)
+ Outfit assembly rules (min 4-6 items, varied retailers)
+ Price tier guidance ($<80 budget, $80-250 mid, $250+ luxury)
```

**User Prompt Pattern:**
```
Receives full StyleProfile JSON serialized inline
Template-injected with clear instructions:
  1. Assign style persona
  2. Match products at each tier (different retailers each time)
  3. Build 3 complete outfits with practical tips
Instructions include CRITICAL rules:
  - NO invented product names ("Cloud Nine Coat" ❌)
  - Plain descriptive names only ("oversized wool coat in camel" ✅)
  - Every outfit item MUST include retailer_hint
```

**Key Implementation Details:**
- Uses same Claude Sonnet model
- Takes serialized StyleProfile JSON as inline context
- Regex JSON extraction + Pydantic validation
- Custom `StyleCuratorError` exception handling
- Logging: persona name, outfit_count, product_count, latency
- No product database queried—uses Claude's knowledge base + placeholder URLs

---

### Orchestration Pattern

**Sequential Chain-of-Thought:**
```python
# From /stylin endpoint (full pipeline)
1. vision_scout.analyze_from_url(image_url) → StyleProfile
2. Measure time elapsed (scout_ms)
3. Pass StyleProfile to style_curator.curate(profile) → CurationResult
4. Measure time elapsed (curator_ms)
5. Return combined response with latency breakdown
```

**Error Handling:**
- Each agent has its own exception class (`VisionScoutError`, `StyleCuratorError`)
- Caught separately with stage-specific error messages
- Timing still recorded; partial data returned if curator fails but scout succeeds
- No retry logic; errors are final

**Session Tracking:**
- Each request generates unique `session_id` (format: `sess_<12-hex>`)
- Passed through both stages for audit logging
- No persistent session storage; just for request tracing

---

## 3. UX Behavior & User Journey

### Frontend Architecture

**Location:** `static/index.html` (single-page HTML + inline CSS + inline JS)

**Key Screens:**
1. **Hero Section**
   - Large serif headline: "See a look you *love*"
   - Subheading: "Drop any photo, get matched outfits across every budget"
   - Tab toggle: Upload vs. URL input
   
2. **Upload/URL Input Panel**
   - Dropzone with drag-and-drop
   - File input accepts JPEG/PNG/WebP
   - Real-time image preview in dropzone
   - URL input field with image preview
   - "Analyze" button with loading state
   
3. **Loading State**
   - Spinner/progress indicator
   - Shows "Vision Scout analyzing..." → "Style Curator building..."
   - Displays latency breakdown when complete

4. **Results Panel** (when available)
   - **Persona Card:** Name, tagline, traits, brand affinity, style icons
   - **Product Tier Cards:** Budget/Mid/Luxury with product image, price, retailer link
   - **Outfit Cards:** 3 complete looks, each with:
     - Outfit name + vibe + occasion
     - Itemized component list with colors + prices
     - Retailer hints for each item
     - One styling tip per outfit

### UX Strengths (What Works Well)

1. **Speed perception**: Latency reporting builds confidence
2. **Visual feedback**: Real-time preview in dropzone, loading spinners
3. **Clarity**: 3-tier structure is immediately scannable (budget vs. mid vs. luxury)
4. **Completeness**: User sees full looks, not just single items
5. **Action-oriented**: Every product/retailer link is clickable → external purchase
6. **Mobile-responsive**: Flexbox layout, touch-friendly dropzone
7. **Accessibility hints**: Tab structure, readable color contrast
8. **Brand voice**: Warm, encouraging language ("That's so you")

### UX Gaps (What's Missing)

1. **No persistence**: Results disappear on page reload (no session storage)
2. **No comparison**: Can't view multiple analyses side-by-side
3. **No personalization**: Every user starts fresh; no StyleProfile storage
4. **No save/share**: No way to save favorite looks or share with others
5. **Limited variation**: Single photo → single curation (no "similar" options)
6. **No retry**: Can't regenerate curator results for same profile
7. **No filtering**: Can't reweight by price tier preference
8. **Assumes connected browser**: Fully cloud-dependent; no offline capability

---

## 4. Technical Reuse Assessment

### ✅ Highly Reusable (Direct Copy)

#### 4.1 Data Models
- **`StyleProfile` (Pydantic)**
  - Complete, well-documented field schema
  - Enum validation for `PriceTier`, `Season`
  - Optional fields handle edge cases
  - **Recommendation:** Use as-is for Stylens; extend with new fields as needed
  - **Location:** [app/models/style_profile.py](app/models/style_profile.py)

- **`CurationResult`, `Outfit`, `OutfitItem`, `MatchedProduct` (Pydantic)**
  - Fully fleshed-out outfit assembly structure
  - Clear separation of concerns (product vs. outfit-level metadata)
  - **Recommendation:** Adapt for Stylens; may need to extend for influencer lookups, geolocation data
  - **Location:** [app/models/curation_result.py](app/models/curation_result.py)

#### 4.2 Agent Patterns & Prompts
- **Vision Scout system + user prompts**
  - Well-structured image analysis instructions
  - Clear JSON output schema + validation rules
  - Handles both URL and base64 image input
  - **Recommendation:** Reuse for initial garment extraction; extend with additional signals (influencer metadata)
  - **Location:** [app/agents/vision_scout.py](app/agents/vision_scout.py#L20-L64)

- **Style Curator prompt template**
  - Excellent structured generation instructions
  - Multi-tier product matching logic
  - Outfit assembly rules (min items, varied retailers, style tips)
  - **CAVEAT:** Assumes simplified product knowledge base; Stylens needs real retailer API integration
  - **Location:** [app/agents/style_curator.py](app/agents/style_curator.py#L25-L166)

#### 4.3 Anthropic Client Wrapper
- **`AnthropicClient` class**
  - Clean abstraction over Anthropic SDK
  - Content block builders for text/image (URL and base64)
  - Single-message dispatch with system prompt + max_tokens
  - **Recommendation:** Use as-is; extend with multi-turn conversation support if needed
  - **Location:** [app/services/anthropic_client.py](app/services/anthropic_client.py)

#### 4.4 Configuration Management
- **`Settings` class (Pydantic Settings)**
  - Secure env var loading (API keys, model names)
  - Sensible defaults (max image size, token limits)
  - **Recommendation:** Extend with new API keys (influencer data, geolocation, retailers)
  - **Location:** [app/config.py](app/config.py)

#### 4.5 Structured Logging
- **JSON logging setup**
  - Structured output to file + stdout
  - Context-rich fields (latency, session_id, error details)
  - **Recommendation:** Use as-is for Stylens; will scale well for multi-agent systems
  - **Location:** [app/utils/logger.py](app/utils/logger.py)

#### 4.6 FastAPI Endpoints & Rate Limiting
- **Endpoint patterns**
  - Clean separation: `/analyze`, `/analyze/upload`, `/curate`, `/stylin` (full pipeline)
  - Proper HTTP status codes, error responses
  - Rate limiting via slowapi
  - **Recommendation:** Extend with new endpoints (e.g., `/social-scout`, `/geo-map`)
  - **Location:** [app/main.py](app/main.py#L90-370)

#### 4.7 Documentation
- **Architecture, API, and PRD docs**
  - Clear system diagrams
  - Request/response contracts
  - Schema examples
  - **Recommendation:** Use as template for Stylens docs; update with new agents
  - **Location:** [readme/](readme/)

---

### ⚠️ Partially Reusable (Adapt for Stylens)

#### 4.8 Frontend UI
- **Current:** Single-photo drop → single recommendation output
- **For Stylens:** Need to add:
  - Influencer lookup UI (search/browse influencer looks)
  - Selection mechanism (choose one influencer look to anchor)
  - Vision Scout output for that influencer look
  - Additional geo-mapping step (show nearby stores)
  - **Recommendation:** Keep upload/analyze components; rebuild results panel for multi-step flow
  - **Location:** [static/index.html](static/index.html)

#### 4.9 Error Handling Pattern
- **Current:** Generic try/catch with custom exceptions
- **Gap:** No retry logic, no backoff, no circuit breaker
- **For Stylens:** With multiple external APIs (influencer data, geo-inventory):
  - Add exponential backoff for transient failures
  - Add circuit breaker for failing services
  - Add per-agent timeout budgets
  - **Recommendation:** Enhance error handling before integrating new APIs
  - **Location:** [app/agents/](app/agents/) and [app/main.py](app/main.py)

---

### ❌ Not Reusable (Build New)

#### 4.10 Influencer / Social Scout Agent
- **Stylin' has no equivalent**
- **Stylens requirement:** Extract influencer looks, find lookalikes, rank by similarity
- **Challenge:** No existing product/influencer matching logic
- **Recommendation:** Design new agent from scratch; may use Vision Scout as starting point for image analysis
- **New Location:** `app/agents/social_scout.py` (or similar)

#### 4.11 Geolocation / Store Inventory Mapping
- **Stylin' has no equivalent**
- **Stylens requirement:** Map extracted outfit to nearby physical stores
- **Challenge:** Requires real inventory APIs, store location databases
- **Recommendation:** Design new mapping service; orchestrate with external retailer APIs
- **New Location:** `app/services/geo_inventory_mapper.py` (or similar)

#### 4.12 Multi-User Persistence & Authentication
- **Stylin' has no auth layer**
- **Stylens requirement:** OAuth2 / session-based user accounts
- **Current architecture:** Stateless agents, optional `user_id` field (unused)
- **Recommendation:** Add persistent user service; extend StyleProfile storage
- **New Location:** `app/services/user_service.py`, database migrations

---

## 5. Implementation Risks

### 🔴 Critical Risks

#### 5.1 No Real Product Database
**Status:** ⚠️ **Blocks MVP**
- **Current state:** Style Curator uses Claude's knowledge base + placeholder URLs
- **Problem:** Product links are fake (`https://asos.com/product/placeholder`)
- **Impact:** Users can't actually purchase; flow breaks at last mile
- **Mitigation:** Implement real retailer API integration before launch
  - ASOS API (requires partnership)
  - Google Shopping API (requires setup)
  - Affiliate network (Rakuten, CJ Affiliate)
  - Manual product data + URLs

#### 5.2 No Influencer Data Source
**Status:** ⚠️ **Blocks Stylens MVP**
- **Current state:** Stylin' has no influencer integration; Stylens requires it
- **Problem:** No established data pipeline for influencer looks/profiles
- **Impact:** Core Stylens feature (find lookalike influencer looks) cannot function
- **Mitigation:** Evaluate data sources:
  - Instagram Business API (limited; requires partner approval)
  - Third-party influencer databases (e.g., HypeAuditor, Grin)
  - Manual curated influencer datasets (faster, less scalable)
  - In-house web scraping (legal/ToS risks)

#### 5.3 No Inventory/Geolocation Integration
**Status:** ⚠️ **Blocks Stylens MVP**
- **Current state:** Stylin' has no store location or inventory mapping
- **Problem:** Stylens requires: "map garments to nearby stores"
- **Impact:** Cannot fulfill core promise; users see products but not where to buy locally
- **Mitigation:** Integrate with:
  - Google Maps API (location context)
  - Retail store locator APIs (Target, Macy's, etc.)
  - Inventory aggregation service (Salsify, Syndigo)

#### 5.4 Single Model Dependency (Claude Sonnet)
**Status:** ⚠️ **Operational Risk**
- **Current state:** Both agents use `claude-sonnet-4-20250514` exclusively
- **Problem:** No fallback; Anthropic outage = service down
- **Impact:** Complete service failure if API is unavailable
- **Mitigation:**
  - Implement fallback to GPT-4o or Gemini
  - Add circuit breaker + graceful degradation
  - Consider local model fallback (Llama) for critical paths
  - Monitor API health proactively

---

### 🟠 High Risks

#### 5.5 Hardcoded Model & Config Values
**Location:** [app/config.py](app/config.py)
```python
anthropic_model: str = Field(default="claude-sonnet-4-20250514", env="ANTHROPIC_MODEL")
vision_max_tokens: int = Field(default=1024, env="VISION_MAX_TOKENS")
curator_max_tokens: int = Field(default=4096, env="CURATOR_MAX_TOKENS")
```
- **Problem:** Defaults are baked in; token limits may be insufficient for Stylens complexity
- **Impact:** Insufficient context for influencer data + outfit details
- **Mitigation:**
  - Validate token limits with extended prompts
  - Add dynamic token budgeting per agent stage
  - Monitor token usage + cost

#### 5.6 No Caching / Memoization
**Status:** 🚩 **Cost & Performance Risk**
- **Current state:** Every identical image re-analyzed from scratch
- **Problem:** Identical garments analyzed multiple times = wasted API calls + latency
- **Impact:** High cost, slow user experience for duplicate searches
- **Mitigation:**
  - Add Redis caching for StyleProfile outputs (keyed by image hash)
  - Cache CurationResult per StyleProfile
  - Set reasonable TTLs (e.g., 24h)
  - Monitor cache hit rate

#### 5.7 Image Upload Parsing Trust Issue
**Location:** [app/main.py#L230](app/main.py#L230)
```python
allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
if file.content_type not in allowed:
    raise HTTPException(...)
```
- **Problem:** Validates MIME type from client; doesn't verify actual file format
- **Impact:** Malicious users could upload wrong format under false MIME type
- **Mitigation:**
  - Add server-side format validation (magic bytes)
  - Use Pillow to verify image on open
  - Consider size/dimension DoS limits

#### 5.8 No Request Validation for Unsafe URLs
**Location:** [app/main.py#L170](app/main.py#L170)
```python
async def analyze_url(request: Request, body: AnalyzeURLRequest) -> AnalyzeResponse:
```
- **Problem:** Accepts any URL; no validation that URL is publicly accessible
- **Impact:** Could expose internal network by requesting private IPs
- **Mitigation:**
  - Validate URL scheme (https only)
  - Blocklist private/reserved IP ranges
  - Add URL length limit
  - Consider rate-limiting per domain

---

### 🟡 Medium Risks

#### 5.9 Rate Limiting Granularity
**Current rates:**
- Vision Scout: 20 req/min per IP
- Full pipeline: 10 req/min per IP

**Problem:** IP-based rate limiting fails behind proxies; no per-user limits
**Impact:** 
- Users behind shared networks may be rate-limited unfairly
- No abuse protection for authenticated users
**Mitigation:**
- Add `X-Forwarded-For` header handling
- Implement per-user rate limits (requires auth)
- Consider token-bucket algorithm over fixed windows

#### 5.10 No Authentication/Authorization
**Current state:** All endpoints are publicly accessible
**Problem:**
  - No user identification
  - No premium tier support
  - No content filtering (could analyze inappropriate images)
**Impact:**
  - Abuse (bot scraping)
  - Cost overruns (no user quota control)
  - Legal liability (offensive content)
**Mitigation:**
  - Add OAuth2 Client Credentials (for server-to-server)
  - Add JWT-based user auth (for browser clients)
  - Add content moderation (NSFW image classification)

#### 5.11 Incomplete Error Messages to User
**Example:** [app/main.py#L190](app/main.py#L190)
```python
return _analyze_error(sid, "An unexpected error occurred. Please try again.", ms)
```
- **Problem:** Generic message; user has no idea what went wrong
- **Impact:** Poor debugging experience; support burden
- **Mitigation:**
  - Log full error server-side; return error code to client
  - Client logs error code for support referral
  - Add structured error response with `error_code` + `error_type` fields

#### 5.12 No Monitoring/Alerting
**Current state:** JSON logs only; no external monitoring
**Problem:**
  - Silent failures (partial pipeline success)
  - No visibility into API quota usage
  - No alert on latency degradation
**Impact:**
  - Undetected outages
  - Cost surprises (Anthropic overage)
  - User experience degradation unnoticed
**Mitigation:**
  - Integrate with monitoring tool (Datadog, New Relic, CloudWatch)
  - Set alerts on error rates, latency, token usage
  - Add synthetic monitoring (periodic test requests)

---

### 🟢 Low Risks

#### 5.13 Open API Documentation in Production
**Status:** Mitigated (disabled in production)
```python
_docs_url = None if _is_production else "/docs"
```
- **Problem:** `/docs` and `/redoc` expose full schema in dev mode
- **Impact:** Low; only if dev instance is exposed
- **Mitigation:** ✅ Already mitigated; disabled in production

#### 5.14 CORS Open to All Origins
```python
CORSMiddleware(
    allow_origins=["*"],  # ⚠️
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
- **Problem:** Any website can call Stylin' API from browser
- **Impact:** Low for public API; higher if auth added
- **Mitigation:** Restrict to known frontend origins before adding auth

---

## 6. Comparison to Intended Stylens Flow

### Intended Stylens User Flow
```
1. User uploads garment
2. Social Scout finds influencer looks/lookalikes
3. User selects one influencer look
4. Vision Scout extracts full outfit (from influencer photo)
5. Geo/inventory maps garments to nearby stores
6. User sees complete outfit + where to buy locally
```

### Gaps Between Stylin' and Stylens

| Step | Stylin' Has | Stylens Needs | Gap Size |
|------|-------------|---------------|----------|
| 1. Upload garment | ✅ Vision Scout analyzes | ✅ Same | None |
| 2. Find influencer looks | ❌ None | ✅ New agent (Social Scout) | **Large** |
| 3. User selects look | ❌ None | ✅ UI component + selection endpoint | **Medium** |
| 4. Extract full outfit | ✅ Vision Scout can do | ✅ Extend Vision Scout | **Small** |
| 5. Geo/inventory mapping | ❌ None | ✅ New service (geo mapper) | **Large** |
| 6. Show stores | ❌ None | ✅ UI component | **Medium** |

### Feature-by-Feature Comparison

#### Photo Analysis (Vision Scout)
| Aspect | Stylin' | Stylens Needed | Gap |
|--------|---------|----------------|-----|
| Input | Single garment photo | Single garment OR influencer photo | Small (same agent) |
| Output | Single item StyleProfile | Full outfit breakdown | **Medium** (need multi-item extraction) |
| Confidence | Single score | Per-item confidence (5+ items) | **Medium** |

**Recommendation:** Extend Vision Scout to:
- Detect multiple items in single photo
- Return array of items with individual confidence scores
- Extract coordination hints ("these items were worn together")

#### Product Matching (Style Curator)
| Aspect | Stylin' | Stylens Needed | Gap |
|--------|---------|----------------|-----|
| Input | StyleProfile (1 item) | StyleProfile (5+ items) | Small |
| Matching | Claude knowledge base | Real retailer APIs | **Large** (new implementation) |
| Output | 3 products (1 per tier) | 5+ products (5 outfit items) | Small |
| Stores | Link to retailer | Link + nearby store location | **Medium** (new geo service) |

**Recommendation:** Build geo/retailer integration service:
- Query Google Maps for store locations
- Query store APIs for inventory
- Add "available at <store>" information to products

#### User Flow Management
| Aspect | Stylin' | Stylens Needed | Gap |
|--------|---------|----------------|-----|
| Sessions | Stateless; no persistence | Multi-step session (upload → search → select → view) | **Large** |
| User profiles | Optional `user_id` field (unused) | Required for saving influencer selections | **Medium** |
| Search/Browse | None | Social Scout results need UI + pagination | **Large** |
| Conversational | Single request/response | Multi-turn (refine search, change filters) | **Large** |

**Recommendation:**
- Add session persistence layer
- Build influencer search UI
- Implement user service for profile storage
- Consider agent conversation memory (e.g., Deploy AI or custom)

---

## 7. Reusable Assets Inventory

### Code Files (Ready to Copy or Extend)

| File | Reuse Level | Purpose | Recommendation |
|------|-------------|---------|-----------------|
| [app/models/style_profile.py](app/models/style_profile.py) | ✅ Direct | Data model for garment analysis | Use as-is; add fields if needed |
| [app/models/curation_result.py](app/models/curation_result.py) | ⚠️ Adapt | Outfit + persona structure | Extend for influencer metadata |
| [app/agents/vision_scout.py](app/agents/vision_scout.py) | ⚠️ Adapt | Image analysis agent | Refactor for multi-item extraction |
| [app/agents/style_curator.py](app/agents/style_curator.py) | ⚠️ Adapt | Outfit recommendation agent | Keep logic; replace product matching |
| [app/services/anthropic_client.py](app/services/anthropic_client.py) | ✅ Direct | API wrapper | Use as-is |
| [app/config.py](app/config.py) | ✅ Direct | Settings management | Extend with new API keys |
| [app/utils/logger.py](app/utils/logger.py) | ✅ Direct | JSON logging | Use as-is |
| [app/main.py](app/main.py) | ⚠️ Adapt | FastAPI app + endpoints | Keep pattern; add new endpoints |
| [static/index.html](static/index.html) | ⚠️ Adapt | Frontend UI | Keep upload/analyze flow; rebuild results |

### Documentation (Template Quality)

| Doc | Quality | Reuse Recommendation |
|-----|---------|----------------------|
| [readme/architecture.md](readme/architecture.md) | High | Use as template for Stylens arch doc |
| [readme/api.md](readme/api.md) | High | Use as template for new endpoints |
| [readme/productrequirements.md](readme/productrequirements.md) | High | Reference for PRD structure |
| [readme/brand_voice.md](readme/brand_voice.md) | High | Reference for Stylens brand alignment |

### Patterns (Methodology)

| Pattern | Reusable | Use For |
|---------|----------|---------|
| Two-agent orchestration | ✅ Yes | Vision Scout + (Social Scout or Geo Mapper) |
| Pydantic input/output contracts | ✅ Yes | All new agents and endpoints |
| System + user prompt separation | ✅ Yes | All new LLM agents |
| JSON-only model output | ✅ Yes | Ensure strict parsing for new agents |
| Regex-based JSON extraction + Pydantic validation | ✅ Yes | Use for all agent responses |
| Rate limiting via slowapi | ✅ Yes | Extend to new endpoints |
| Session ID generation + logging | ✅ Yes | Maintain for audit trail |

---

## 8. Non-Reusable Assets

### Components Specific to Stylin' (Not Applicable to Stylens)

| Component | Why Not Reusable | Stylens Alternative |
|-----------|------------------|-------------------|
| Single-item StyleProfile extraction | Stylens needs multi-item breakdown | Extend Vision Scout schema |
| Placeholder product URLs | Stylens needs real retailer links | Implement geo-aware product service |
| Named style personas (format: "The X Y") | Acceptable but may not fit Stylens brand | Adapt format if needed |
| Budget/Mid/Luxury 3-tier structure | Useful; may expand to 4-5 tiers in Stylens | Keep pattern; parameterize tier count |
| Claude-only agent setup | Works fine; may want fallback models | Consider multi-model strategy |

### MVP Shortcuts That Need Refactoring

| Shortcut | Current State | Why It's Limited | Stylens Fix |
|----------|---------------|--------------------|------------|
| Product data | Claude's knowledge base | Becomes stale; no retailer partnerships | Real API integration |
| Influencer data | None exists | Can't find lookalikes | New Social Scout agent + data source |
| Store locations | None | No local fulfillment | Geo mapper service + store APIs |
| User persistence | Stateless | Can't track preferences | User service + database |
| Multi-step flow | Single pipeline | No iterative refinement | Session management + conversation state |

---

## 9. Recommended Refactor Candidates

### Priority 1: Enable Real Product Matching (Blocks MVP)

**Current State:**
```python
# From style_curator.py prompt:
"Use DIFFERENT retailers for each tier — never repeat"
"URLs format: 'https://<retailer-domain>/product/placeholder'"
```

**Problem:** All URLs are fake; users can't actually shop

**Proposed Solution:**
```python
# New service: app/services/product_matcher.py

class ProductMatcher:
    """Queries real APIs for products matching style signals."""
    
    async def match_products(
        self, 
        style_profile: StyleProfile, 
        price_tiers: list[str]
    ) -> list[MatchedProduct]:
        """
        Query ASOS, Google Shopping, etc. for real products.
        Return valid product URLs + current prices.
        """
        # 1. Search each retailer API
        # 2. Rank by style signal match (use Vision Scout output)
        # 3. Filter by price tier
        # 4. Return real MatchedProduct objects
```

**Implementation Steps:**
1. Evaluate retailer API partnerships (ASOS, Google Shopping, Rakuten)
2. Design product scoring algorithm (match to color/style_tags)
3. Build ProductMatcher service
4. Integrate into Style Curator pipeline
5. Add product caching layer (Redis)

**Estimated Effort:** 3–4 weeks (including API onboarding)

---

### Priority 2: Add Multi-Item Vision Extraction (Prep for Stylens)

**Current State:**
```python
# vision_scout.py returns single StyleProfile
{
  "item_type": "midi dress",  # Single item only
  "colors": ["sage green"],
  ...
}
```

**Problem:** Stylens needs to extract 5+ items from influencer photo

**Proposed Solution:**
```python
# Extend vision_scout.py or create new agent:

class VisionScoutMultiItem:
    """Extracts multiple items from a single photo."""
    
    def analyze_from_url(self, image_url: str) -> list[StyleProfile]:
        """
        Detect all garments in photo.
        Return array of StyleProfiles (one per item).
        Annotate relationships ("worn together").
        """
```

**Implementation Steps:**
1. Rewrite Vision Scout prompt to request item array
2. Add output schema for multi-item response
3. Add parser logic to validate array structure
4. Add tests with outfit photos (multiple items)
5. Create transition endpoint `/analyze/multi` initially

**Estimated Effort:** 1–2 weeks (prompt refinement + testing)

---

### Priority 3: Extract Geo/Store Mapping as Service (Enables Stylens)

**Current State:**
None; product links point to global retailers

**Proposed Solution:**
```python
# New service: app/services/geo_inventory_mapper.py

class GeoInventoryMapper:
    """Maps products to nearby physical stores."""
    
    async def find_stores(
        self,
        products: list[MatchedProduct],
        user_location: tuple[lat, lng],
        radius_km: float = 10
    ) -> list[StoreWithInventory]:
        """
        Query Google Maps for stores matching retailers.
        Query store APIs for inventory.
        Return: stores + in-stock items + distances.
        """

# New endpoint: POST /geo/map
async def map_products_to_stores(
    products: list[MatchedProduct],
    lat: float,
    lng: float
) -> list[StoreWithInventory]:
    """Maps outfit to nearby stores."""
```

**Implementation Steps:**
1. Integrate Google Maps API for store locator
2. Build retailer-specific inventory APIs (Target, Macy's, etc.)
3. Design StoreWithInventory response schema
4. Add geolocation detection (browser or manual entry)
5. Add caching for store/inventory data (1h TTL)

**Estimated Effort:** 2–3 weeks (API integration + geolocation)

---

### Priority 4: Add User Persistence Layer (Enables Personalization)

**Current State:**
```python
# Unused user_id field in requests
user_id: Optional[str] = None
```

**Problem:** No profile storage; every session is anonymous

**Proposed Solution:**
```python
# New service: app/services/user_service.py
# New models: app/models/user_profile.py

class UserProfile(BaseModel):
    """Extends StyleProfile with persistence + preferences."""
    user_id: str
    style_persona_history: list[StylePersona]  # Track persona changes
    liked_products: list[str]  # Product IDs
    disliked_styles: list[str]
    preferred_colors: list[str]
    size_data: dict  # {"top": "M", "bottom": "28"}
    created_at: datetime
    updated_at: datetime

# Database: Simple PostgreSQL with SQLAlchemy ORM
```

**Implementation Steps:**
1. Add PostgreSQL database + SQLAlchemy setup
2. Create user_service.py with CRUD operations
3. Add JWT authentication (session tokens)
4. Extend endpoints to load UserProfile
5. Add `/profile` endpoints (GET, PUT)
6. Modify agents to use user history (personalized recommendations)

**Estimated Effort:** 3–4 weeks (auth + database + integration)

---

### Priority 5: Add Social Scout Agent (Core Stylens Feature)

**Current State:**
None

**Proposed Solution:**
```python
# New agent: app/agents/social_scout.py

class SocialScout:
    """Finds influencer looks matching a garment."""
    
    async def find_lookalike_influencers(
        self,
        style_profile: StyleProfile,
        limit: int = 10
    ) -> list[InfluencerLook]:
        """
        Given a garment, find influencers who've worn similar items.
        Use external influencer data API (HypeAuditor, etc.).
        Return ranked list of influencer photos + metadata.
        """
```

**Implementation Steps:**
1. Evaluate influencer data sources (HypeAuditor, Grin, Instagram API)
2. Design InfluencerLook schema (influencer_name, look_image_url, engagement, etc.)
3. Build SocialScout agent (Claude + retrieval of influencer DB)
4. Add new endpoints:
   - POST `/social-scout/find` — find lookalikes
   - GET `/social-scout/influencers/<id>` — get influencer profile
5. Extend frontend with influencer browse/select UI

**Estimated Effort:** 4–6 weeks (data sourcing + API integration + UI)

---

## 10. Implementation Risks for Stylens Adaptation

### Risk Matrix

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|-----------|
| Multi-API orchestration fails | **High** | Partial results; poor UX | Add circuit breaker + fallback per service |
| Influencer data stale/incomplete | **High** | Poor recommendation quality | Implement refresh strategy + data QA |
| Geolocation privacy concerns | **Medium** | Legal liability + user backlash | Add privacy policy + opt-in consent |
| Real product API rate limits | **Medium** | Latency spikes | Add caching + queue/batching |
| Handling multi-item extraction errors | **Medium** | Incomplete outfits | Add validation + user re-prompts |
| Session state explosion (multi-turn) | **Medium** | Memory/cost overruns | Implement TTLs + state size limits |

---

## 11. Open Questions for Architect

### Strategic

1. **Influencer Data Source:** Will you partner with an influencer platform (HypeAuditor, Grin) or build your own influencer scraper? (Timeline & cost implications)

2. **Real Product Data:** Will Stylens integrate with ASOS/Google Shopping APIs or build a manual product database initially? (Affects product freshness + accuracy)

3. **Geolocation Strategy:** Browser-based geolocation, user input, or reverse-geocode from store address? (Privacy + UX tradeoffs)

4. **User Authentication:** OAuth2 (social sign-in) or email/password? (User friction vs. data quality)

5. **Brand Voice:** Does Stylens keep Stylin''s "cool friend" tone or adopt different personality? (Affects prompt rewriting)

### Technical

6. **Database Choice:** PostgreSQL (relational) or document-based (MongoDB)? (Schema flexibility + query patterns)

7. **Agent Memory:** Will Stylens support multi-turn conversation (e.g., "refine the outfit with more budget options") or single-turn requests? (Affects architecture; Deploy AI has conversation memory)

8. **Fallback Models:** Should we add GPT-4o/Gemini fallback to Claude, or accept Anthropic dependency? (Cost + resilience tradeoff)

9. **Real-time Inventory:** Will you sync store inventory in real-time or use hourly/daily snapshots? (Cost + freshness tradeoff)

10. **Fashion Taxonomy:** Should Stylens use Stylin''s existing style tags (cottagecore, minimalist, etc.) or expand/customize? (Affects model training + user perception)

### Operational

11. **Monitoring & Observability:** Will Stylens use Datadog, CloudWatch, or in-house logging? (Budget + alerting depth)

12. **Cost Budgeting:** What's the per-request cost target (including all APIs: Anthropic, Google Maps, influencer data)? (Affects caching strategy + feature prioritization)

13. **MVP Scope:** Are all 6 steps required for launch, or can some be deferred (e.g., geo mapping in v2)? (Affects timeline + complexity)

14. **Legal/Compliance:** Are there ToS/GDPR concerns with:
    - Scraping influencer content?
    - Storing user geolocation?
    - Retail affiliate links?
    (Affects data sourcing + disclosure requirements)

---

## 12. Summary & Recommendations

### Stylin' Did Well ✅

1. **Agent Orchestration Pattern** — Clean separation of Vision Scout (analysis) and Style Curator (curation); easy to extend
2. **Data Contracts** — Pydantic models provide type safety + documentation
3. **Prompt Engineering** — Excellent structured-output prompts with clear JSON schemas
4. **Error Handling** — Custom exception classes + latency tracking
5. **Logging** — JSON structured logs enable easy parsing + analysis
6. **Documentation** — Clear architecture + API docs; good for knowledge transfer
7. **Frontend Simplicity** — Single-page HTML with real-time preview and loading states

### Stylin' Limitations (for Stylens) ⚠️

1. **No Product Database** — Placeholder URLs only; must integrate real retailers
2. **Single-Item Only** — Vision Scout designed for one garment; Stylens needs outfit extraction
3. **No Influencer Integration** — Entire "Social Scout" feature missing
4. **No Geolocation** — Can't map to nearby stores
5. **Stateless** — No user profiles or session memory
6. **No Authentication** — Public API only
7. **No Multi-turn Flow** — Designed for single request/response

### Reuse Roadmap for Stylens

**Phase 1 (Week 1–2): Foundation**
- Copy data models (StyleProfile, CurationResult, Outfit)
- Copy Anthropic client wrapper + config
- Copy logging + error handling patterns
- Adapt main.py FastAPI setup

**Phase 2 (Week 3–4): Core Analysis**
- Adapt Vision Scout for multi-item extraction
- Build ProductMatcher service (integrate real APIs)
- Build GeoInventoryMapper service (Google Maps)
- Add endpoints: `/analyze/multi`, `/geo/map`

**Phase 3 (Week 5–8): Influencer Integration**
- Build SocialScout agent (evaluate data sources first)
- Design influencer lookup UI
- Implement search + selection flow
- Integrate Social Scout → Vision Scout → Geo Mapper pipeline

**Phase 4 (Week 9+): Persistence & Polish**
- Add user service + authentication
- Add session management for multi-step flow
- Add product/influencer caching
- Launch with full Stylens flow (6 steps)

### Estimated Full Stylens Build Time

- **Minimum (core only):** 8–10 weeks
- **With full features:** 12–16 weeks
- **Critical path blocker:** Influencer data source (requires external partnership)

---

## Appendix A: Code Locations Reference

| Component | File | Lines |
|-----------|------|-------|
| StyleProfile schema | [app/models/style_profile.py](app/models/style_profile.py) | 1–80 |
| CurationResult schema | [app/models/curation_result.py](app/models/curation_result.py) | 1–150 |
| Vision Scout agent | [app/agents/vision_scout.py](app/agents/vision_scout.py) | 1–180 |
| Vision Scout prompts | [app/agents/vision_scout.py](app/agents/vision_scout.py#L20-L64) | 20–64 |
| Style Curator agent | [app/agents/style_curator.py](app/agents/style_curator.py) | 1–300 |
| Style Curator prompts | [app/agents/style_curator.py](app/agents/style_curator.py#L25-L166) | 25–166 |
| Anthropic client | [app/services/anthropic_client.py](app/services/anthropic_client.py) | 1–140 |
| FastAPI endpoints | [app/main.py](app/main.py) | 100–370 |
| Rate limiting | [app/main.py](app/main.py#L50-L58) | 50–58 |
| Frontend UI | [static/index.html](static/index.html) | 1–650 |
| Structured logging | [app/utils/logger.py](app/utils/logger.py) | 1–80 |

---

## Document Metadata

**Author:** Technical Review for Architect  
**Date:** 2026-05-03  
**Scope:** Comprehensive codebase review (analysis only, no code changes)  
**Next Step:** Share with Architect; discuss open questions and refactor priorities  
**Review Status:** ✅ Complete
