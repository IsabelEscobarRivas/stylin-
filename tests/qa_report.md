# Stylin' QA Report

> Generated: 2026-03-02 09:08 UTC  
> Backend: `http://localhost:3000`  
> Overall: **✅ ALL PASS** — 47/47 checks passed

---

## T1 — Health Check — GET /health

**Result:** ✅ PASS
**Latency:** 3ms

| Check | Status | Detail |
|-------|--------|--------|
| HTTP 200 | ✅ | Got 200 |
| body.status == "ok" | ✅ | body={'status': 'ok', 'version': '1.0.0', 'environment': 'development'} |
| Response is JSON | ✅ | application/json |
| Latency < 500ms | ✅ | 3ms |

---

## T2 — Full Pipeline — POST /stylin (fashion image URL)

**Result:** ✅ PASS
**Latency:** 31,426ms

| Check | Status | Detail |
|-------|--------|--------|
| HTTP 200 | ✅ | Got 200 |
| success == true | ✅ | success=True |
| StyleProfile present | ✅ | missing style_profile key |
| StyleProfile.item_type | ✅ | item_type='long coat' |
| StyleProfile.colors (≥1) | ✅ | colors=['powder blue', 'blush pink', 'cream'] |
| StyleProfile.style_tags (≥1) | ✅ | style_tags=['european chic', 'sophisticated', 'layered', 'modest fashion'] |
| StyleProfile.occasion (≥1) | ✅ | occasion=['sightseeing', 'travel', 'city exploration'] |
| StyleProfile.price_tier (≥1) | ✅ | price_tier=['mid-range'] |
| CurationResult present | ✅ | missing curation_result key |
| matched_products == 3 | ✅ | got 3 products |
| outfits == 3 | ✅ | got 3 outfits |
| product[0] tier∈{budget,mid-range,luxury} | ✅ | tier='budget' |
| product[0] has name+retailer+url | ✅ | name='wool blend long coat in light blue' retailer='H&M' url='https://hm.com/product/placeholder' |
| product[1] tier∈{budget,mid-range,luxury} | ✅ | tier='mid-range' |
| product[1] has name+retailer+url | ✅ | name='wool blend oversized coat in dusty pink' retailer='& Other Stories' url='https://stories.com/product/placeholder' |
| product[2] tier∈{budget,mid-range,luxury} | ✅ | tier='luxury' |
| product[2] has name+retailer+url | ✅ | name='wool cashmere long coat in cream' retailer='Toteme' url='https://toteme-studio.com/product/placeholder' |
| style_persona not empty | ✅ | persona={'name': 'The Refined Wanderer', 'tagline': 'effortless sophistication meets travel-ready practicality', 'defini |
| style_persona.tagline | ✅ | tagline='effortless sophistication meets travel-ready practicality' |
| style_persona.defining_traits ≥3 | ✅ | traits=['elevated basics', 'soft color palette', 'polished layers'] |
| outfit[0] has name | ✅ | name='parisian morning' |
| outfit[0] items ≥3 | ✅ | got 5 items |
| outfit[1] has name | ✅ | name='museum wanderer' |
| outfit[1] items ≥3 | ✅ | got 5 items |
| outfit[2] has name | ✅ | name='spring café hopping' |
| outfit[2] items ≥3 | ✅ | got 5 items |
| Total latency < 40s | ✅ | 31.43s (budget=40s) |

**Snapshot:**
```json
{
  "style_profile": {
    "item_type": "long coat",
    "colors": [
      "powder blue",
      "blush pink",
      "cream"
    ],
    "style_tags": [
      "european chic",
      "sophisticated",
      "layered",
      "modest fashion"
    ],
    "occasion": [
      "sightseeing",
      "travel",
      "city exploration"
    ],
    "price_tier": [
      "mid-range"
    ],
    "confidence_score": 0.85
  },
  "style_persona": {
    "name": "The Refined Wanderer",
    "tagline": "effortless sophistication meets travel-ready practicality"
  },
  "products_tiers": [
    "budget",
    "mid-range",
    "luxury"
  ],
  "latency": {
    "total_ms": 31421,
    "vision_scout_ms": 3725,
    "style_curator_ms": 27695
  }
}
```

---

## T3 — Edge Cases

**Result:** ✅ PASS

| Check | Status | Detail |
|-------|--------|--------|
| 3a: landscape → no server crash (< 500) | ✅ | HTTP 200 |
| 3a: landscape → meaningful response body | ✅ | body keys=['success', 'session_id', 'error', 'stage', 'latency_ms'] |
| 3b: empty upload → 422 validation error | ✅ | HTTP 422 |
| 3c: large file → 413 or graceful 4xx | ✅ | HTTP 413 |
| 3c: large file → no server crash (< 500) | ✅ | HTTP 413 |

---

## T4 — UI Checks — Source Analysis + Live API Probes

**Result:** ✅ PASS

| Check | Status | Detail |
|-------|--------|--------|
| 4.1: All 3 price tier cards (Budget/Mid/Luxury) defined in source | ✅ | budget=True mid-range=True luxury=True |
| 4.1b: renderProducts() function generates tier cards | ✅ | renderProducts=True tier-labels=True |
| 4.2a: fetchPexelsImages() function present in source | ✅ | function=True api_url=True |
| 4.2b: Pexels image CSS classes used for <img> elements | ✅ | product-pexels-img / outfit-pexels-img classes found |
| 4.2c: Pexels API returns real photos (not placeholders) | ✅ | HTTP 200, photos=1 |
| 4.3: Product links generate Google Shopping URLs | ✅ | google_shop_url=True shop-btn-class=True |
| 4.4: Outfit card items rendered with Google Shopping links | ✅ | outfit-item-row+google=True renderOutfits=True |
| 4.5: 'Analyze another photo' button + resetUI() function present | ✅ | btn=True fn=True text=True |
| 4.live: Pipeline returns all 3 tiers for tier cards | ✅ | tiers={'mid-range', 'budget', 'luxury'} |
| 4.live: All matched_products have url (→ clickable links) | ✅ | urls present: [True, True, True] |
| 4.live: All outfits have ≥3 items (→ Google Shopping rows) | ✅ | item_counts=[5, 5, 5] |

---

## Summary

| Test | Title | Result | Checks |
|------|-------|--------|--------|
| T1 | Health Check — GET /health | ✅ PASS | 4/4 |
| T2 | Full Pipeline — POST /stylin (fashion image URL) | ✅ PASS | 27/27 |
| T3 | Edge Cases | ✅ PASS | 5/5 |
| T4 | UI Checks — Source Analysis + Live API Probes | ✅ PASS | 11/11 |

---

*Report auto-generated by `tests/run_qa.py` on 2026-03-02 09:08 UTC*