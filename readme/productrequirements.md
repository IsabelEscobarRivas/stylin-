# Stylin' — Product Requirements Document (PRD)

**Version:** 1.0 | **Date:** 2026-03-02 | **Status:** Active
**Owner:** product | **Stakeholder:** Isabel Escobar Rivas

---

## 1. Executive Summary

Stylin' is an AI-powered fashion discovery platform that eliminates the friction between finding a look you love and knowing how to make it your own. Users drop any photo, and the platform returns three complete outfit builds across every budget — instantly.

**The core problem:** Fashion inspiration is everywhere. Actually buying the look is fragmented, impersonal, and budget-blind.

**The solution:** A two-agent AI system that reads visual inspiration and returns shoppable, budget-matched outfits tailored to the user's evolving style identity.

---

## 2. Problem Statement

| Pain Point | Current State | Stylin' Solution |
|---|---|---|
| Inspiration → purchase gap | Manual search across multiple sites | One photo → complete shoppable looks |
| No personalization | Generic recommendations | StyleProfile powers ongoing personalization |
| Budget mismatch | Recommendations ignore price reality | Every look delivered at 3 budget tiers |
| Style identity confusion | Users don't know how to describe their style | Style Persona gives users a named identity |

---

## 3. Target Users

### Persona 1: The Trend Chaser
- **Age:** 18–28
- **Behavior:** Scrolls TikTok/Instagram for inspiration, shops impulsively
- **Need:** Fast, culturally fluent recommendations that match what they're seeing online
- **Success metric:** Time from inspiration to product in cart < 60 seconds

### Persona 2: The Conscious Stylist
- **Age:** 25–40
- **Behavior:** Thoughtful buyer, quality-aware, builds a considered wardrobe
- **Need:** Recommendations that match personal aesthetic, not trends; multiple price options
- **Success metric:** Repeat session rate; StyleProfile accuracy score

### Persona 3: The Gifter
- **Age:** Any
- **Behavior:** Shopping for someone else; uncertain, needs guidance
- **Need:** Clear, confidence-building guidance; easily shareable results
- **Success metric:** Gift-mode completion rate; share/copy link usage

---

## 4. Goals & Success Metrics

### Business Goals
- Launch MVP with core Vision Scout + Style Curator pipeline
- Achieve product-market fit with Trend Chaser persona first
- Build StyleProfile data layer as long-term moat

### Success Metrics (MVP)

| Metric | Target |
|---|---|
| Inspiration → shoppable look | < 10 seconds |
| Budget tier coverage | 100% of recommendations in all 3 tiers |
| Style Persona assignment accuracy | > 80% user satisfaction |
| StyleProfile update rate | > 60% users return and trigger updates |
| Session-to-product-click rate | > 40% |

---

## 5. Core Features (MVP)

### 5.1 Vision Scout — Image Analysis

**Description:** User drops any photo (screenshot, saved image, camera shot). Vision Scout analyzes it and extracts fashion signals.

**Acceptance Criteria:**
- [ ] Accepts image via URL or file upload
- [ ] Extracts: garment types, color palette, style tags, occasion context
- [ ] Returns structured signal object in < 3 seconds
- [ ] Handles unreadable/low-quality images with graceful fallback message
- [ ] Confidence score returned with every analysis

**Out of scope (MVP):** Video analysis, multiple simultaneous image comparison

---

### 5.2 Style Curator — Outfit Recommendations

**Description:** Receives style signals from Vision Scout (or direct text input) and returns three complete outfit builds across budget tiers.

**Acceptance Criteria:**
- [ ] Returns exactly 3 budget tiers: Budget / Mid-range / Splurge
- [ ] Each tier contains a complete outfit (minimum: top + bottom or dress, shoes, one accessory)
- [ ] Each item includes: product name, price, retailer, product link
- [ ] Recommendations respect StyleProfile preferences if available
- [ ] Response includes Style Persona name (assigned or updated)
- [ ] Response time < 8 seconds end-to-end

**Out of scope (MVP):** Physical store locations, AR try-on

---

### 5.3 StyleProfile — Persistent Style Identity

**Description:** A user data object that persists across sessions and powers ongoing personalization.

**Acceptance Criteria:**
- [ ] Created on first interaction
- [ ] Stores: style persona, preferred colors, disliked styles, size data, saved items, budget preference
- [ ] Updates automatically after each session
- [ ] User can view and manually edit profile
- [ ] Data treated as PII — access controlled

---

### 5.4 Style Persona Assignment

**Description:** A named style identity assigned to the user based on their interaction history and StyleProfile.

**Examples:** The Romantic Minimalist, The Street-Smart Maximalist, The Classic Neutralist

**Acceptance Criteria:**
- [ ] Assigned after minimum 3 interactions
- [ ] Updated if style signals shift significantly
- [ ] Displayed to user in a celebratory, branded way ("That's so you.")
- [ ] Used to pre-filter recommendations in all future sessions

---

## 6. Non-Functional Requirements

| Category | Requirement |
|---|---|
| Performance | End-to-end recommendation < 10 seconds |
| Availability | 99.5% uptime target |
| Security | OAuth2 auth; no PII in logs; HTTPS only |
| Scalability | Stateless agents; horizontally scalable |
| Logging | JSON logs to `logs/` directory; all agent events logged |
| Error handling | All agent failures return user-friendly messages; no raw errors exposed |

---

## 7. Out of Scope (v1.0)

- Native mobile apps (web-first)
- Social sharing / community features
- Brand partnerships / paid placement
- AR try-on
- Video input analysis
- Direct purchase / checkout (links only in MVP)

---

## 8. User Flow (MVP)

```
1. User lands on Stylin'
         │
2. User drops a photo (or describes a look in text)
         │
3. Vision Scout analyzes image → returns style signals
         │
4. Style Curator builds 3-tier outfit recommendations
         │
5. User sees: 3 complete looks (Budget / Mid / Splurge)
         │
6. User clicks into a look → sees individual items with links
         │
7. StyleProfile updated → Style Persona displayed
         │
8. User saves items / shares look / starts new search
```

---

## 9. Open Questions

| Question | Owner | Status |
|---|---|---|
| Which retailers are integrated at launch? | product | Open |
| Is StyleProfile stored per session or account-based (login required)? | architect | Open |
| What is the gift mode UX flow? | product | Open |
| How are product links sourced — affiliate API or scraping? | architect | Open |

---

## 10. Dependencies

| Dependency | Type | Notes |
|---|---|---|
| Deploy AI Platform | External | Agent hosting, orchestration |
| Product Retailer APIs | External | TBD — required before launch |
| Brand Voice Profile | Internal | Governs all copy and agent tone |
| StyleProfile schema | Internal | Must be finalized before Style Curator build |

---

*Owner: product | References: Isabel Escobar Rivas brief (2026-03-02), Brand_Voice_Profile.md*
