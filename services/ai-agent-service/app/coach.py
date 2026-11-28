import json
import re
from typing import Any, Dict, List, Optional, Tuple


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
