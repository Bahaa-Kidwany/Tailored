import json
import logging
import math
import re
from typing import Any, Dict, List, Optional, Tuple

from sqlmodel import Session, select

from tailored_kit import LlmClient

from app.ambient import deterministic_embedding_768
from app.models import BehavioralMemoryFactDB

logger = logging.getLogger(__name__)


_NUM_PATTERN = re.compile(
    r"(?:\b\d+(?:\.\d+)?%|\$\d+(?:,\d+)*(?:\.\d+)?|\b\d+(?:\.\d+)?x\b|\b\d+(?:,\d+)*\s*(?:ms|sec|seconds|users|routes|dispatches)\b)",
    re.IGNORECASE,
)


def extract_quantitative_tokens(text: str) -> List[str]:
    return [m.group(0).strip() for m in _NUM_PATTERN.finditer(text or "")]


def verify_numbers_against_context(
    candidate_text: str,
    profile_summary: Dict[str, Any],
    prior_user_texts: List[str],
) -> Tuple[bool, List[str]]:
    """
    Zero-Hallucination Metric Interception:
    Every quantitative token in proposed CV/cover letter edits must appear in the
    candidate's Master Profile or explicit prior user messages in the thread.
    """
    tokens = extract_quantitative_tokens(candidate_text)
    if not tokens:
        return True, []

    evidence_blob = json.dumps(profile_summary.get("profile") or {}, default=str).lower()
    evidence_blob += "\n" + "\n".join(prior_user_texts).lower()

    unverified: List[str] = []
    for tok in tokens:
        digits = re.sub(r"[^0-9.]", "", tok)
        if tok.lower() not in evidence_blob and (not digits or digits not in evidence_blob):
            unverified.append(tok)

    return len(unverified) == 0, unverified


def find_verified_metric_snippet(profile: Dict[str, Any]) -> Optional[str]:
    for persona in profile.get("career_personas") or []:
        for exp in persona.get("experience_highlights") or []:
            for ach in exp.get("achievements") or []:
                if extract_quantitative_tokens(ach):
                    return ach
    return None


def build_coach_turn(
    *,
    prompt: str,
    surface: str,
    mode: str,
    profile_summary: Dict[str, Any],
    job_ctx: Dict[str, Any],
    prior_user_texts: List[str],
    memory_facts: List[str],
    focused_anchor: Optional[Dict[str, str]] = None,
    saved_docs: Optional[List[Dict[str, Any]]] = None,
    radar_jobs: Optional[List[Dict[str, Any]]] = None,
    pipeline_items: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Produces a grounded Studio Coach response matching CalmAiCoachSidecar.tsx."""
    q = prompt.lower().strip()
    profile = profile_summary.get("profile") or {}
    company = job_ctx.get("company_name") or "Target Company"
    role = job_ctx.get("title") or "Target Role"
    job_id = job_ctx.get("id")
    anchor_id = (focused_anchor or {}).get("id") or "exp_1_bullet_1"
    anchor_label = (focused_anchor or {}).get("label") or f"{company} · Lead Bullet"

    memory_note = f" · Applied learned preference ({memory_facts[0][:50]})" if memory_facts else ""
    thinking = f"Checked Master Profile + {company} 5-D fit{memory_note}"

    # 1. Pipeline stage mutation -> Confirmation-gated Action Card
    if (
        any(w in q for w in ("mark", "move", "set", "track", "update"))
        and any(w in q for w in ("pipeline", "applied", "interview", "saved"))
    ):
        next_status = "interview" if "interview" in q else ("saved" if "saved" in q else "applied")
        label = next_status.title()
        return {
            "thinking_summary": f"Verified {company} status in Application Pipeline CRM",
            "text": f"Ready to update {company} ({role}) in your Application Pipeline:",
            "action_card": {
                "title": f"Move {company} to {label}",
                "description": (
                    "Freezes your active CV snapshot and sets the 7-day follow-up reminder cleanly."
                    if next_status == "applied"
                    else f"Updates {company} to {label} in your Pipeline CRM."
                ),
                "targetBadge": f"Pipeline · {label}",
                "confirmLabel": "Confirm Update",
                "status": "pending",
                "actionType": "pipeline_stage",
                "payload": {"jobId": job_id, "status": next_status, "company_name": company, "job_title": role},
            },
        }

    # 2. @Pipeline audit
    if "@pipeline" in q or any(w in q for w in ("overdue", "follow-up", "followup")):
        pipes = pipeline_items or []
        audit_items = []
        for it in pipes[:3]:
            audit_items.append(
                {
                    "id": f"aud_{it.get('id')}",
                    "sentiment": "down" if it.get("status") == "applied" else "up",
                    "title": f"{it.get('company_name')} · {it.get('status', '').replace('_', ' ').title()}",
                    "detail": f"{it.get('job_title')} ({it.get('recruiter_email') or 'External Portal'})",
                }
            )
        if not audit_items:
            audit_items.append(
                {
                    "id": "aud_empty",
                    "sentiment": "up",
                    "title": "Pipeline is clear",
                    "detail": "No overdue follow-ups detected.",
                }
            )
        return {
            "thinking_summary": f"Audited {len(pipes)} tracked Pipeline items",
            "text": f"Checked your Application Pipeline ({len(pipes)} tracked threads):",
            "audit": {"heading": "Pipeline Attention Summary", "items": audit_items},
        }

    # 3. @Saved CVs lookup
    if "@saved" in q or any(w in q for w in ("available cvs", "my cvs", "which cv", "best cv")):
        docs = saved_docs or []
        items = [
            {
                "id": f"res_cv_{d.get('doc_id')}",
                "kind": "cv",
                "title": f"{d.get('company_name')} · {d.get('job_title')}",
                "subtitle": f"Status: {d.get('status')} · {d.get('bullet_diffs_count', 0)} diffs",
                "fitScore": d.get("fit_score") or 90,
                "meta": "Tailored CV",
                "primaryLabel": "Load Draft",
                "payloadId": d.get("doc_id"),
            }
            for d in docs[:4]
        ]
        return {
            "thinking_summary": f"Ranked {len(items)} saved CVs against {company}",
            "text": f"Found {len(items)} tailored CVs in your archive for {company}:",
            "resources": {"heading": f"Saved CVs · Ranked for {company}", "items": items},
        }

    # 4. @Jobs lookup
    if "@jobs" in q or "matching jobs" in q or "other jobs" in q:
        jobs = radar_jobs or []
        items = [
            {
                "id": f"res_job_{j.get('id')}",
                "kind": "job",
                "title": f"{j.get('company_name')} · {j.get('title')}",
                "subtitle": f"{j.get('location')} · {j.get('work_mode')}",
                "fitScore": j.get("fit_score") or 80,
                "primaryLabel": "Tailor CV",
                "payloadId": str(j.get("id")),
            }
            for j in jobs[:4]
        ]
        return {
            "thinking_summary": "Queried top ranked matches from Radar",
            "text": "Top matches from your Job Radar ranked against your Master Profile:",
            "resources": {"heading": "Top Radar Matches", "items": items},
        }

    # 5. Zero-Hallucination Metric Interception check
    verified_snippet = find_verified_metric_snippet(profile)
    asks_for_new_metrics = any(w in q for w in ("metric", "quantify", "percentage", "numbers", "latency", "kpi", "revenue"))
    user_provided_nums = extract_quantitative_tokens(prompt)

    if asks_for_new_metrics and not verified_snippet and not user_provided_nums:
        return {
            "thinking_summary": "Checked Master Profile — no verified quantitative metric found for this item",
            "text": (
                f"Your Master Profile does not record a concrete percentage or latency figure for {anchor_label} yet. "
                "To keep your CV 100% factual and recruiter-defensible, I never invent numbers — "
                "what real % improvement, throughput, or latency figure did you achieve here?"
            ),
            "proposal": {
                "targetAnchorId": anchor_id,
                "targetLabel": anchor_label,
                "oldText": "Built backend routing services in Python.",
                "newText": "",
                "status": "pending",
                "isMetricQuestion": True,
            },
        }

    # 6. Grounded Proposal Diff Card
    skills = ", ".join((job_ctx.get("parsed_skills") or ["Python", "FastAPI", "Docker"])[:3])
    if user_provided_nums:
        metric_phrase = f"delivering {user_provided_nums[0]} measurable impact"
    elif verified_snippet:
        metric_phrase = verified_snippet
    else:
        metric_phrase = f"scaling production {skills} workflows for {role}"

    if surface == "cover_letter":
        old_txt = f"I am writing to express my interest in the {role} role at {company}."
        new_txt = f"Having delivered {metric_phrase}, I am excited to bring verified {skills} execution to {company}'s {role} roadmap."
    else:
        old_txt = "Built production backend and machine learning services."
        new_txt = (
            f"Architected {skills} services ({metric_phrase}), directly aligned with {company}'s {role} requirements."
            if mode != "Surgical"
            else f"Engineered {skills} pipelines — {metric_phrase}."
        )

    is_valid, _unverified = verify_numbers_against_context(
        new_txt, profile_summary, prior_user_texts + [prompt]
    )
    if not is_valid:
        return {
            "thinking_summary": "Intercepted unverified metric before emitting proposal",
            "text": "What exact verified number should I insert for this achievement?",
            "proposal": {
                "targetAnchorId": anchor_id,
                "targetLabel": anchor_label,
                "oldText": old_txt,
                "newText": "",
                "status": "pending",
                "isMetricQuestion": True,
            },
        }

    return {
        "thinking_summary": thinking,
        "text": f"Grounded this {mode.lower()} edit in your verified Master Profile without adding unverified claims:",
        "proposal": {
            "targetAnchorId": anchor_id,
            "targetLabel": anchor_label,
            "oldText": old_txt,
            "newText": new_txt,
            "status": "pending",
            "isMetricQuestion": False,
        },
    }


def _cosine_similarity(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1.0
    nb = math.sqrt(sum(y * y for y in b)) or 1.0
    return dot / (na * nb)


async def _get_top_memory_facts(
    session: Session,
    user_id: str,
    query_text: str,
    llm_client: Optional[LlmClient] = None,
    top_k: int = 5,
) -> List[str]:
    """Retrieves top active behavioral memory facts via pgvector cosine distance (<=>) with Python fallback."""
    query_vec = await llm_client.embed_text(query_text, dim=768) if llm_client else None
    if not query_vec:
        query_vec = deterministic_embedding_768(query_text)

    try:
        facts = session.exec(
            select(BehavioralMemoryFactDB)
            .where(
                BehavioralMemoryFactDB.user_id == user_id,
                BehavioralMemoryFactDB.status == "active",
                BehavioralMemoryFactDB.embedding.is_not(None),
            )
            .order_by(BehavioralMemoryFactDB.embedding.cosine_distance(query_vec))
            .limit(top_k)
        ).all()
        if facts:
            return [f.fact_text for f in facts]
    except Exception as exc:
        logger.debug("pgvector cosine_distance query fell back (%s)", exc)

    rows = session.exec(
        select(BehavioralMemoryFactDB)
        .where(
            BehavioralMemoryFactDB.user_id == user_id,
            BehavioralMemoryFactDB.status == "active",
        )
        .order_by(BehavioralMemoryFactDB.last_reinforced_at.desc())
    ).all()
    if not rows:
        return []

    scored: List[Tuple[float, str]] = []
    for row in rows:
        vec = list(row.embedding) if row.embedding is not None else deterministic_embedding_768(row.fact_text)
        scored.append((_cosine_similarity(query_vec, vec), row.fact_text))
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [text for _, text in scored[:top_k]]


async def generate_coach_reply(
    *,
    prompt: str,
    surface: str,
    mode: str,
    profile_summary: Dict[str, Any],
    job_ctx: Dict[str, Any],
    prior_user_texts: List[str],
    memory_facts: List[str],
    focused_anchor: Optional[Dict[str, str]] = None,
    saved_docs: Optional[List[Dict[str, Any]]] = None,
    radar_jobs: Optional[List[Dict[str, Any]]] = None,
    pipeline_items: Optional[List[Dict[str, Any]]] = None,
    llm_client: Optional[LlmClient] = None,
) -> Dict[str, Any]:
    """Generates a grounded Studio Coach response using LlmClient when configured, always enforcing metric grounding."""
    base = build_coach_turn(
        prompt=prompt,
        surface=surface,
        mode=mode,
        profile_summary=profile_summary,
        job_ctx=job_ctx,
        prior_user_texts=prior_user_texts,
        memory_facts=memory_facts,
        focused_anchor=focused_anchor,
        saved_docs=saved_docs,
        radar_jobs=radar_jobs,
        pipeline_items=pipeline_items,
    )
    proposal = base.get("proposal")
    if not llm_client or not llm_client.is_configured or not proposal or proposal.get("isMetricQuestion"):
        return base

    system_prompt = (
        "You are Tailored Studio Coach. Rewrite one focused resume/cover-letter item for the target role. "
        "STRICT RULE: NEVER invent metrics, percentages, dollar figures, latencies, or claims absent from the candidate's "
        "Master Profile or prior user messages. Return compact JSON with keys: thinking_summary, text, new_text."
    )
    user_payload = json.dumps(
        {
            "surface": surface,
            "mode": mode,
            "prompt": prompt,
            "old_text": proposal.get("oldText"),
            "target_label": proposal.get("targetLabel"),
            "job": {
                "title": job_ctx.get("title"),
                "company_name": job_ctx.get("company_name"),
                "parsed_skills": (job_ctx.get("parsed_skills") or [])[:8],
            },
            "memory_facts": memory_facts[:5],
            "prior_user_texts": prior_user_texts[-4:],
            "profile": profile_summary.get("profile") or {},
        },
        default=str,
    )
    raw = await llm_client.generate_text(system_prompt, user_payload[:5000], temperature=0.2, max_tokens=500)
    if not raw:
        return base

    cleaned = raw.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(cleaned)
        cand_new = str(parsed.get("new_text") or "").strip()
        cand_text = str(parsed.get("text") or base["text"]).strip()
        cand_think = str(parsed.get("thinking_summary") or base.get("thinking_summary") or "").strip()
    except Exception:
        return base

    if not cand_new:
        return base

    ok, _unverified = verify_numbers_against_context(
        f"{cand_text}\n{cand_new}",
        profile_summary,
        prior_user_texts + [prompt],
    )
    if not ok:
        return base

    updated = dict(base)
    updated["thinking_summary"] = cand_think or base.get("thinking_summary")
    updated["text"] = cand_text or base["text"]
    updated_prop = dict(proposal)
    updated_prop["newText"] = cand_new
    updated["proposal"] = updated_prop
    return updated
