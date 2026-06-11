# SkySignal Source Validation Pipeline

This document describes how raw data from external sources flows through SkySignal's validation pipeline before becoming a confirmed incident that affects threat scores.

---

## Design Principle

**No external data source — GDELT, RSS, NewsAPI, or any automated feed — ever auto-promotes an incident to APPROVED status.**

All externally-sourced candidates enter with:
- `review_status = PENDING`
- `confidence_tier = UNVERIFIED`
- `confidence_score = 0–30` (depending on source credibility)

Human review is required for APPROVED status. This prevents automated threat score inflation from unreliable news or synthetic data.

---

## Data Entry Points

### 1. Manual SALUTE Report

A user submits a first-hand observation via the SALUTE form (`/apps/api/app/routers/salute.py`).

- Creates a `salute_reports` record with `review_status = PENDING`.
- An admin can promote the SALUTE to a linked `incidents` record.
- SALUTE-sourced incidents start with `confidence_tier = LOW` (score ~20) until corroborated.

### 2. Automated Feed Import (GDELT / RSS / NewsAPI)

The ingestion services (`gdelt_service.py`, `official_validation_service.py`) create candidate incident records when enabled via feature flags.

- **GDELT:** Full-text news corpus; high volume, low per-article reliability.
- **RSS/NewsAPI:** Targeted news feeds; medium reliability.
- **FAA UAS Sightings CSV:** Official dataset; high reliability — auto-boosts confidence on import.

All automated imports produce incidents with `review_status = PENDING`.

### 3. Official Press / FAA Direct Import

Content sourced directly from official government press releases, FAA DroneZone data, or DOJ/DHS/FBI statements.

If the `official_match_score ≥ 80`, the importer may set:
- `confidence_tier = HIGH` or `VERIFIED`
- `confidence_score` boosted accordingly

These still enter as `PENDING` for human sign-off before APPROVED.

---

## Evidence Roles

Every piece of evidence linked to an incident carries an `evidence_role` that determines its effect on the confidence score.

| Role | Effect | Description |
|---|---|---|
| `DISCOVERY` | Base (no bonus) | The first piece of evidence that identified the incident. Every incident has exactly one discovery item. |
| `CORROBORATION` | +10 to +20 pts | A second (or later) independent source confirming the incident occurred. Official source corroborations score higher. |
| `OFFICIAL_CONFIRMATION` | +20 to +40 pts | Explicit confirmation by a government agency, law enforcement, or aviation authority. Official sources score +40; unverified claims of official confirmation score +20. |
| `CONTRADICTION` | −15 pts | Evidence that casts doubt on the incident's occurrence or key details. Analysts should add this when a source retracts or disputes. |
| `DUPLICATE` | No score change | The same incident as another record — used for deduplication workflow. |
| `REJECTION_SUPPORT` | No score change | Evidence supporting the decision to REJECT an incident. Preserved for audit trail. |

---

## Confidence Score Computation

Implemented in `apps/api/app/services/confidence_service.py`. Recomputes whenever evidence is added, updated, or removed.

### Algorithm

```
score = 0

for each evidence item:
  if role == OFFICIAL_CONFIRMATION:
    if source.is_official: score += 40
    else:                   score += 20
  if role == CORROBORATION:
    if source.is_official: score += 20
    else:                   score += 10
  if role == CONTRADICTION:
    score -= 15

# Bonus for multiple corroborating sources (independent diversity)
corroboration_count = count of CORROBORATION items
if corroboration_count >= 2: score += min((corroboration_count - 1) * 5, 20)

score = clamp(score, 0, 100)
```

### Score → Tier mapping

| Score | Tier |
|---|---|
| 80–100 | `VERIFIED` |
| 60–79 | `HIGH` |
| 40–59 | `MEDIUM` |
| 20–39 | `LOW` |
| 0–19 | `UNVERIFIED` |

---

## Official Match Score

The `official_match_score` (0–100) on both `incidents` and `incident_evidence` records quantifies how closely the content matches an independently retrieved official account.

Computed by `apps/api/app/services/official_validation_service.py`.

### Component weights

| Component | Max Points | Method |
|---|---|---|
| Date match | 25 | Exact date = 25, within 3 days = 15, within 7 days = 5 |
| Location match | 25 | Geocoded distance: <1 km = 25, <5 km = 15, <25 km = 5 |
| Facility match | 20 | Named entity match on facility/location name |
| Incident type match | 15 | Type classification agreement |
| Jurisdiction match | 10 | Same city/county/state as the official account |
| Named entity match | 5 | Shared organization/agency names |

**Threshold:** `official_match_score ≥ 80` triggers automatic confidence boost. The incident is not auto-approved — it is elevated to `IN_REVIEW` for analyst confirmation.

---

## Review Workflow

```
PENDING ──────────────────────────────────────► APPROVED
   │                                              │
   ├──► IN_REVIEW ──► APPROVED                   │ (contributes to threat scores,
   │         │                                   │  visible on map)
   │         └──► NEEDS_MORE_REVIEW ──► IN_REVIEW
   │
   └──► REJECTED
         │
         └─ (audit log preserved; never deleted)
```

### State transitions

| From | To | Trigger |
|---|---|---|
| `PENDING` | `IN_REVIEW` | Admin opens the record in the review queue |
| `IN_REVIEW` | `APPROVED` | Admin clicks Approve (creates audit log entry) |
| `IN_REVIEW` | `REJECTED` | Admin clicks Reject with reason |
| `IN_REVIEW` | `NEEDS_MORE_REVIEW` | Admin flags for additional evidence gathering |
| `NEEDS_MORE_REVIEW` | `IN_REVIEW` | New evidence added; analyst re-queues |
| `PENDING` | `APPROVED` | High official_match_score (≥80) + automated pipeline rule (future feature) |
| `REJECTED` | `IN_REVIEW` | Override by ORG_ADMIN with justification |

All transitions are written to `audit_logs` with `old_values` and `new_values`.

---

## Source Credibility

Each `sources` record has a `credibility_score` (0–100) and `is_official` flag.

| Source Type | Typical Credibility | `is_official` |
|---|---|---|
| `OFFICIAL_PRESS` (DOJ, DHS, FBI, FAA) | 90–100 | true |
| `FAA` (DroneZone, ASRS) | 95–100 | true |
| `SENSOR` (DragonSync/WarDragon) | 70–85 | false (depends on deployment) |
| `RSS` (established news outlets) | 50–70 | false |
| `GDELT` | 30–50 | false |
| `NEWSAPI` | 40–60 | false |
| `MANUAL` (internal analyst) | 60–80 | false |

The `is_official` flag is set by platform administrators when adding a source — it is not self-reported by the source itself.

---

## Admin Review Queue

The review queue is exposed at `GET /api/admin/review-queue` (requires `ORG_ADMIN` or `SUPER_ADMIN` role).

Returns incidents with `review_status IN ('PENDING', 'IN_REVIEW', 'NEEDS_MORE_REVIEW')` sorted by:
1. `official_match_score DESC` (high-confidence candidates first)
2. `occurred_at DESC` (most recent events first)

Each queue item includes:
- Full incident fields
- Linked evidence items with role and source
- Official match score breakdown
- SALUTE report (if linked)
- Audit log history

### Approve / Reject API

```
PATCH /api/admin/incidents/{id}/approve
PATCH /api/admin/incidents/{id}/reject
body: { reason: string }
```

Both endpoints:
1. Update `review_status` and (for approve) `confidence_tier`
2. Write an `audit_logs` record
3. Trigger `ConfidenceService.recompute()` on the incident
4. (Future) Evaluate watch zone alerts for newly approved incidents
