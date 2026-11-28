import hashlib
import json
import math
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import redis.asyncio as aioredis
from sqlmodel import Session, select

from tailored_kit import LlmClient

from app.models import (
    BehavioralMemoryFactDB,
    ProactiveSuggestionDB,
    UserBehaviorProfileDB,
    utc_now,
)


def deterministic_embedding_768(text: str) -> List[float]:
    """Deterministic 768-dim L2-normalized embedding for pgvector HNSW similarity search."""
    vec: List[float] = []
    seed = text.encode("utf-8")
    counter = 0
    while len(vec) < 768:
        digest = hashlib.sha256(seed + counter.to_bytes(4, "big")).digest()
        for i in range(0, len(digest), 2):
            if len(vec) >= 768:
                break
            val = int.from_bytes(digest[i : i + 2], "big", signed=True) / 32768.0
            vec.append(val)
        counter += 1
    norm = math.sqrt(sum(v * v for v in vec)) or 1.0
    return [v / norm for v in vec]


def update_tier0_behavior_aggregates(
    session: Session,
    *,
    user_id: str,
    event_id: str,
    event_name: str,
    feature_key: str,
    persona_track: str,
    payload: Dict[str, Any],
) -> UserBehaviorProfileDB:
    """Tier 0 deterministic behavioral aggregator (zero LLM cost)."""
    prof = session.get(UserBehaviorProfileDB, user_id)
    if not prof:
        prof = UserBehaviorProfileDB(user_id=user_id)
        session.add(prof)
        session.flush()

    locs = json.loads(prof.dominant_locations_json or "{}")
    roles = json.loads(prof.implicit_role_drift_json or "{}")
    style = json.loads(prof.writing_style_prefs_json or "{}")
    gaps = json.loads(prof.skill_gap_clicks_json or "{}")
    props = payload.get("properties") or {}

    if event_name == "ui.job.dwelled" or feature_key == "radar.job.dwell":
        country = str(props.get("job_country") or props.get("country") or "Unknown")
        role = str(props.get("normalized_role") or persona_track or "Engineer")
        locs[country] = int(locs.get(country, 0)) + 1
        roles[role] = int(roles.get(role, 0)) + 1
    elif event_name == "ui.job.hidden" or feature_key == "radar.job.hide":
        country = str(props.get("job_country") or "Unknown")
        locs[f"hidden:{country}"] = int(locs.get(f"hidden:{country}", 0)) + 1
    elif event_name == "ui.skill_gap.clicked" or feature_key == "job.skill_gap.click":
        sk = str(props.get("skill_token") or "Unknown")
        gaps[sk] = int(gaps.get(sk, 0)) + 1
    elif event_name == "ui.proposal.resolved":
        res = str(props.get("resolution") or "")
        refine = str(props.get("refine_preset") or "")
        if res == "applied":
            style["applied"] = int(style.get("applied", 0)) + 1
        elif res == "skipped":
            style["skipped"] = int(style.get("skipped", 0)) + 1
        elif res == "refined" and refine:
            style[f"refine:{refine}"] = int(style.get(f"refine:{refine}", 0)) + 1
        total_res = int(style.get("applied", 0)) + int(style.get("skipped", 0))
        if total_res > 0:
            prof.avg_proposal_accept_rate = round(int(style.get("applied", 0)) / total_res, 3)

    prof.dominant_locations_json = json.dumps(locs)
    prof.implicit_role_drift_json = json.dumps(roles)
    prof.writing_style_prefs_json = json.dumps(style)
    prof.skill_gap_clicks_json = json.dumps(gaps)
    prof.total_events_processed += 1
    prof.events_since_last_distill += 1
    prof.updated_at = utc_now()
    session.add(prof)
    session.flush()
    return prof


def _upsert_memory_fact(
    session: Session,
    *,
    user_id: str,
    category: str,
    fact_text: str,
    source_event_id: str,
    confidence: float = 0.85,
    embedding: Optional[List[float]] = None,
) -> BehavioralMemoryFactDB:
    vec = embedding if embedding is not None else deterministic_embedding_768(fact_text)
    existing = session.exec(
        select(BehavioralMemoryFactDB).where(
            BehavioralMemoryFactDB.user_id == user_id,
            BehavioralMemoryFactDB.category == category,
            BehavioralMemoryFactDB.status == "active",
        )
    ).first()
    if existing:
        existing.fact_text = fact_text
        existing.embedding = vec
        existing.confidence = confidence
        src_ids = json.loads(existing.source_event_ids_json or "[]")
        if source_event_id not in src_ids:
            src_ids = (src_ids + [source_event_id])[-20:]
        existing.source_event_ids_json = json.dumps(src_ids)
        existing.last_reinforced_at = utc_now()
        session.add(existing)
        session.flush()
        return existing

    fact = BehavioralMemoryFactDB(
        user_id=user_id,
        category=category,
        fact_text=fact_text,
        embedding=vec,
        confidence=confidence,
        source_event_ids_json=json.dumps([source_event_id]),
    )
    session.add(fact)
    session.flush()
    return fact


async def evaluate_distillation_and_proactive_rules(
    session: Session,
    redis_client: aioredis.Redis,
    *,
    prof: UserBehaviorProfileDB,
    latest_event_id: str,
    llm_client: Optional[LlmClient] = None,
) -> Tuple[List[BehavioralMemoryFactDB], Optional[Dict[str, Any]]]:
    """
    Tier 1 memory distillation + Calm Proactive Suggestion evaluation with strict cooldowns.
    Never mutates Master Profile or spends credits autonomously.
    """
    distilled: List[BehavioralMemoryFactDB] = []
    emitted_suggestion: Optional[Dict[str, Any]] = None

    async def _store_fact(category: str, fact_text: str) -> BehavioralMemoryFactDB:
        emb = await llm_client.embed_text(fact_text, dim=768) if llm_client else None
        return _upsert_memory_fact(
            session,
            user_id=prof.user_id,
            category=category,
            fact_text=fact_text,
            source_event_id=latest_event_id,
            embedding=emb,
        )

    locs = json.loads(prof.dominant_locations_json or "{}")
    roles = json.loads(prof.implicit_role_drift_json or "{}")
    style = json.loads(prof.writing_style_prefs_json or "{}")
    gaps = json.loads(prof.skill_gap_clicks_json or "{}")

    # Distill grounded memory facts whenever thresholds are met (or >= 5 signals)
    for role, cnt in roles.items():
        if not role.startswith("hidden:") and cnt >= 4:
            distilled.append(
                await _store_fact(
                    "role_drift",
                    f"Frequently dwells on {role} opportunities ({cnt} recent sessions).",
                )
            )

    for loc, cnt in locs.items():
        if not loc.startswith("hidden:") and loc != "Unknown" and cnt >= 4:
            distilled.append(
                await _store_fact(
                    "location_drift",
                    f"Shows strong browsing affinity for {loc} roles ({cnt} dwell signals).",
                )
            )

    for key, cnt in style.items():
        if key.startswith("refine:") and cnt >= 3:
            pref = key.split(":", 1)[1]
            distilled.append(
                await _store_fact(
                    "writing_style",
                    f"Prefers '{pref}' bullet phrasing during Studio CV refinements.",
                )
            )

    for sk, cnt in gaps.items():
        if sk != "Unknown" and cnt >= 3:
            distilled.append(
                await _store_fact(
                    "skill_gap",
                    f"Repeatedly inspects missing '{sk}' skill requirements across target jobs.",
                )
            )

    if distilled:
        prof.events_since_last_distill = 0
        prof.last_distilled_at = utc_now()
        session.add(prof)

    # Check proactive suggestion rules + Redis cooldown
    global_cd_key = f"ai:nudge:cooldown:{prof.user_id}:global"
    if await redis_client.get(global_cd_key):
        return distilled, None

    candidate: Optional[Tuple[str, str, str, str]] = None
    top_role = max(((r, c) for r, c in roles.items() if not r.startswith("hidden:")), key=lambda x: x[1], default=None)
    top_gap = max(gaps.items(), key=lambda x: x[1], default=None)
    top_loc = max(((l, c) for l, c in locs.items() if not l.startswith("hidden:") and l != "Unknown"), key=lambda x: x[1], default=None)

    if top_role and top_role[1] >= 5:
        candidate = (
            "persona_drift_detected",
            f"Exploring {top_role[0]} roles lately?",
            f"You've dwelled on {top_role[1]} {top_role[0]} roles — spin up a dedicated persona track in Master Profile?",
            "/profile",
        )
    elif top_gap and top_gap[1] >= 4:
        candidate = (
            "recurring_skill_gap_bridge",
            f"Recurring gap check: {top_gap[0]}",
            f"{top_gap[1]} roles you viewed mention {top_gap[0]}. Bridge your adjacent architecture work in Studio?",
            "/studio",
        )
    elif top_loc and top_loc[1] >= 4:
        candidate = (
            "location_mobility_shift",
            f"Seeing more {top_loc[0]} roles in your browsing",
            f"Add {top_loc[0]} as an active Radar search location for better daily matches?",
            "/profile",
        )

    if candidate:
        rule_key, title, body, cta_route = candidate
        already = session.exec(
            select(ProactiveSuggestionDB).where(
                ProactiveSuggestionDB.user_id == prof.user_id,
                ProactiveSuggestionDB.rule_key == rule_key,
            )
        ).first()
        if not already:
            sugg = ProactiveSuggestionDB(
                user_id=prof.user_id,
                rule_key=rule_key,
                title=title,
                body=body,
                cta_route=cta_route,
                payload_json=json.dumps({"total_events": prof.total_events_processed}),
            )
            session.add(sugg)
            session.flush()
            await redis_client.setex(global_cd_key, 48 * 3600, "1")
            emitted_suggestion = {
                "suggestion_id": sugg.id,
                "user_id": prof.user_id,
                "rule_key": rule_key,
                "title": title,
                "body": body,
                "cta_route": cta_route,
            }

    return distilled, emitted_suggestion
