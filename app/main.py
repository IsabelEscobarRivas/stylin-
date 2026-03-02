"""
main.py — Stylin' Backend API (FastAPI)

Endpoints:
  GET  /health              — liveness check
  POST /analyze             — Agent 1 Vision Scout: image URL → StyleProfile
  POST /analyze/upload      — Agent 1 Vision Scout: file upload → StyleProfile
  POST /curate              — Agent 2 Style Curator: StyleProfile → CurationResult
  POST /stylin              — Full pipeline: image URL → StyleProfile → CurationResult
  POST /stylin/upload       — Full pipeline: file upload → StyleProfile → CurationResult

Security:
  - Rate limiting via slowapi:
      /stylin, /stylin/upload  → 10 req/min/IP
      /analyze, /analyze/upload → 20 req/min/IP
      /health                  → unlimited
  - /docs and /redoc disabled in production (APP_ENV=production)
  - API keys loaded from .env only; never exposed in responses or logs
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import Optional

import httpx

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.agents.vision_scout import VisionScoutError, vision_scout
from app.agents.style_curator import StyleCuratorError, style_curator
from app.config import settings
from app.models.requests import (
    AnalyzeResponse,
    AnalyzeURLRequest,
    CurateRequest,
    CurateResponse,
    HealthResponse,
)
from app.utils.logger import get_logger

logger = get_logger("stylin.main")

# ── Rate limiter ───────────────────────────────────────────────────────────────
# Uses client IP as the partition key; falls back gracefully behind proxies
limiter = Limiter(key_func=get_remote_address, default_limits=[])


# ── App lifecycle ─────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Stylin' backend starting",
        extra={"env": settings.app_env, "model": settings.anthropic_model}
    )
    yield
    logger.info("Stylin' backend shutting down")


# ── FastAPI app ───────────────────────────────────────────────────────────────
# Disable interactive docs in production to prevent API schema exposure
_is_production = settings.app_env.lower() == "production"
_docs_url = None if _is_production else "/docs"
_redoc_url = None if _is_production else "/redoc"

app = FastAPI(
    title="Stylin' API",
    description=(
        "AI-powered visual fashion intelligence backend.\n\n"
        "**Agent 1 — Vision Scout:** Analyzes a fashion image → `StyleProfile`\n\n"
        "**Agent 2 — Style Curator:** Builds 3 outfits + persona → `CurationResult`\n\n"
        "**Full pipeline:** `/stylin` chains both agents end-to-end."
    ),
    version="1.0.0",
    docs_url=_docs_url,
    redoc_url=_redoc_url,
    lifespan=lifespan,
)

# Attach the rate limiter to the app state
app.state.limiter = limiter

# Custom 429 handler — returns the required message
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many requests — try again in a minute"},
    )

# CORS — open for MVP; restrict to domain in production as needed
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files (frontend UI)
app.mount("/static", StaticFiles(directory="static"), name="static")


# ── Helpers ───────────────────────────────────────────────────────────────────

def _new_session_id() -> str:
    return f"sess_{uuid.uuid4().hex[:12]}"


def _analyze_error(sid: str, msg: str, ms: int) -> AnalyzeResponse:
    return AnalyzeResponse(success=False, session_id=sid, error=msg, latency_ms=ms)


def _curate_error(sid: str, msg: str, ms: int) -> CurateResponse:
    return CurateResponse(success=False, session_id=sid, error=msg, latency_ms=ms)


# ── System ────────────────────────────────────────────────────────────────────

@app.get("/", include_in_schema=False)
async def serve_frontend():
    return FileResponse("static/index.html")


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["System"],
    summary="Liveness check — unlimited rate",
)
async def health_check() -> HealthResponse:
    """Returns service status — used by load balancers and monitoring. No rate limit."""
    return HealthResponse(status="ok", version="1.0.0", environment=settings.app_env)


# ── Agent 1: Vision Scout ─────────────────────────────────────────────────────

@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["Vision Scout"],
    summary="Analyze a fashion image via URL",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
async def analyze_url(request: Request, body: AnalyzeURLRequest) -> AnalyzeResponse:
    """
    **Agent 1 — Vision Scout**

    Pass a public image URL. Returns a `StyleProfile` with item type, colors,
    style tags, occasion, price tier, season, and confidence score.

    Rate limit: 20 requests/minute/IP
    Latency target: ≤ 5s (p95)
    """
    sid = _new_session_id()
    t0 = time.monotonic()
    logger.info("analyze_url", extra={"session_id": sid})  # URL omitted to avoid logging sensitive paths

    try:
        profile = vision_scout.analyze_from_url(body.image_url)
    except VisionScoutError as e:
        ms = int((time.monotonic() - t0) * 1000)
        return _analyze_error(sid, str(e), ms)
    except Exception:
        ms = int((time.monotonic() - t0) * 1000)
        logger.error("Unexpected error in analyze_url", extra={"session_id": sid}, exc_info=True)
        return _analyze_error(sid, "An unexpected error occurred. Please try again.", ms)

    ms = int((time.monotonic() - t0) * 1000)
    logger.info("analyze_url complete", extra={"session_id": sid, "latency_ms": ms})
    return AnalyzeResponse(success=True, session_id=sid, style_profile=profile, latency_ms=ms)


@app.post(
    "/analyze/upload",
    response_model=AnalyzeResponse,
    tags=["Vision Scout"],
    summary="Analyze an uploaded fashion image",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("20/minute")
async def analyze_upload(
    request: Request,
    file: UploadFile = File(..., description="Fashion image (JPEG, PNG, WebP)"),
    user_id: Optional[str] = Form(default=None),
) -> AnalyzeResponse:
    """
    **Agent 1 — Vision Scout** (file upload variant)

    Upload a fashion photo as multipart/form-data.
    Accepted formats: JPEG, PNG, WebP | Max size: 10MB
    Rate limit: 20 requests/minute/IP
    """
    sid = _new_session_id()
    t0 = time.monotonic()

    allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type not in allowed:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type '{file.content_type}'. Use JPEG, PNG, or WebP."
        )

    image_bytes = await file.read()
    if len(image_bytes) > settings.max_image_size_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"Image exceeds the {settings.max_image_size_mb}MB limit."
        )

    logger.info("analyze_upload", extra={"session_id": sid, "size": len(image_bytes)})  # filename omitted

    try:
        profile = vision_scout.analyze_from_bytes(image_bytes, mime_type=file.content_type)
    except VisionScoutError as e:
        ms = int((time.monotonic() - t0) * 1000)
        return _analyze_error(sid, str(e), ms)
    except Exception:
        ms = int((time.monotonic() - t0) * 1000)
        logger.error("Unexpected error in analyze_upload", extra={"session_id": sid}, exc_info=True)
        return _analyze_error(sid, "An unexpected error occurred. Please try again.", ms)

    ms = int((time.monotonic() - t0) * 1000)
    logger.info("analyze_upload complete", extra={"session_id": sid, "latency_ms": ms})
    return AnalyzeResponse(success=True, session_id=sid, style_profile=profile, latency_ms=ms)


# ── Agent 2: Style Curator ────────────────────────────────────────────────────

@app.post(
    "/curate",
    response_model=CurateResponse,
    tags=["Style Curator"],
    summary="Build outfits + persona from a StyleProfile",
    status_code=status.HTTP_200_OK,
)
async def curate(request: CurateRequest) -> CurateResponse:
    """
    **Agent 2 — Style Curator**

    Pass a `StyleProfile` (from `/analyze`). Returns a `CurationResult` with:
    - A named style persona + tagline + defining traits
    - 3 matched products: one each at budget / mid-range / luxury
    - 3 complete, shoppable outfit recommendations

    Latency target: ≤ 10s (p95)
    """
    sid = _new_session_id()
    t0 = time.monotonic()
    logger.info("curate", extra={"session_id": sid, "item_type": request.style_profile.item_type})

    try:
        result = style_curator.curate(request.style_profile)
    except StyleCuratorError as e:
        ms = int((time.monotonic() - t0) * 1000)
        return _curate_error(sid, str(e), ms)
    except Exception:
        ms = int((time.monotonic() - t0) * 1000)
        logger.error("Unexpected error in curate", extra={"session_id": sid}, exc_info=True)
        return _curate_error(sid, "An unexpected error occurred. Please try again.", ms)

    ms = int((time.monotonic() - t0) * 1000)
    logger.info("curate complete", extra={"session_id": sid, "persona": result.style_persona.name, "latency_ms": ms})
    return CurateResponse(success=True, session_id=sid, curation_result=result, latency_ms=ms)


# ── Full pipeline: /stylin ────────────────────────────────────────────────────

@app.post(
    "/stylin",
    tags=["Full Pipeline"],
    summary="Full pipeline: image URL → StyleProfile → CurationResult",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
async def stylin_url(request: Request, body: AnalyzeURLRequest):
    """
    **Full Pipeline** — chains Vision Scout → Style Curator end-to-end.

    Pass a public image URL; receive `StyleProfile` + `CurationResult` in one call.
    Rate limit: 10 requests/minute/IP
    Total latency target: ≤ 15s (p95)
    """
    sid = _new_session_id()
    t0 = time.monotonic()
    logger.info("stylin_url", extra={"session_id": sid})

    # Stage 1: Vision Scout
    try:
        profile = vision_scout.analyze_from_url(body.image_url)
    except Exception as e:
        ms = int((time.monotonic() - t0) * 1000)
        return {"success": False, "session_id": sid, "error": str(e), "stage": "vision_scout", "latency_ms": ms}

    scout_ms = int((time.monotonic() - t0) * 1000)

    # Stage 2: Style Curator
    t1 = time.monotonic()
    try:
        result = style_curator.curate(profile)
    except Exception as e:
        total_ms = int((time.monotonic() - t0) * 1000)
        return {"success": False, "session_id": sid, "error": str(e), "stage": "style_curator",
                "style_profile": profile.model_dump(), "latency_ms": total_ms}

    curator_ms = int((time.monotonic() - t1) * 1000)
    total_ms = int((time.monotonic() - t0) * 1000)

    logger.info("stylin_url complete", extra={"session_id": sid, "total_ms": total_ms, "persona": result.style_persona.name})
    return {
        "success": True,
        "session_id": sid,
        "style_profile": profile.model_dump(),
        "curation_result": result.model_dump(),
        "latency": {"total_ms": total_ms, "vision_scout_ms": scout_ms, "style_curator_ms": curator_ms},
    }


@app.get(
    "/pexels/search",
    tags=["Proxy"],
    summary="Server-side Pexels image search — key never exposed to clients",
    include_in_schema=not _is_production,
)
async def pexels_search(q: str, per_page: int = 3, orientation: str = "landscape"):
    """
    Proxies a Pexels search server-side so PEXELS_KEY is never sent to the browser.
    The key is read from .env via Settings; it is never included in any response.
    """
    if not settings.pexels_key:
        return {"photos": []}

    url = "https://api.pexels.com/v1/search"
    params = {"query": q, "per_page": per_page, "orientation": orientation}
    try:
        async with httpx.AsyncClient(timeout=8) as client:
            r = await client.get(
                url, params=params,
                headers={"Authorization": settings.pexels_key}
            )
            r.raise_for_status()
            data = r.json()
            # Return only the fields the frontend needs; key is never forwarded
            return {"photos": [{"src": p["src"]} for p in data.get("photos", [])]}
    except Exception:
        logger.warning("Pexels proxy request failed", exc_info=False)
        return {"photos": []}


@app.post(
    "/stylin/upload",
    tags=["Full Pipeline"],
    summary="Full pipeline: file upload → StyleProfile → CurationResult",
    status_code=status.HTTP_200_OK,
)
@limiter.limit("10/minute")
async def stylin_upload(
    request: Request,
    file: UploadFile = File(..., description="Fashion image (JPEG, PNG, WebP)"),
    user_id: Optional[str] = Form(default=None),
):
    """
    **Full Pipeline** (file upload variant) — chains Vision Scout → Style Curator.

    Upload a photo; receive `StyleProfile` + `CurationResult` in one call.
    Rate limit: 10 requests/minute/IP
    """
    sid = _new_session_id()
    t0 = time.monotonic()

    allowed = {"image/jpeg", "image/png", "image/webp", "image/jpg"}
    if file.content_type not in allowed:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                            detail="Unsupported file type. Use JPEG, PNG, or WebP.")

    image_bytes = await file.read()
    if len(image_bytes) > settings.max_image_size_bytes:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                            detail=f"Image exceeds {settings.max_image_size_mb}MB limit.")

    # Stage 1
    try:
        profile = vision_scout.analyze_from_bytes(image_bytes, mime_type=file.content_type)
    except Exception as e:
        ms = int((time.monotonic() - t0) * 1000)
        return {"success": False, "session_id": sid, "error": str(e), "stage": "vision_scout", "latency_ms": ms}

    scout_ms = int((time.monotonic() - t0) * 1000)

    # Stage 2
    t1 = time.monotonic()
    try:
        result = style_curator.curate(profile)
    except Exception as e:
        total_ms = int((time.monotonic() - t0) * 1000)
        return {"success": False, "session_id": sid, "error": str(e), "stage": "style_curator",
                "style_profile": profile.model_dump(), "latency_ms": total_ms}

    curator_ms = int((time.monotonic() - t1) * 1000)
    total_ms = int((time.monotonic() - t0) * 1000)

    logger.info("stylin_upload complete", extra={"session_id": sid, "total_ms": total_ms, "persona": result.style_persona.name})
    return {
        "success": True,
        "session_id": sid,
        "style_profile": profile.model_dump(),
        "curation_result": result.model_dump(),
        "latency": {"total_ms": total_ms, "vision_scout_ms": scout_ms, "style_curator_ms": curator_ms},
    }
