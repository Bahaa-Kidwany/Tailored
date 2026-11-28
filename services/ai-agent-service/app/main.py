from __future__ import annotations

import asyncio
import json
import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional
from uuid import uuid4

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, Query, Request, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, delete, text
from sqlmodel import Session, SQLModel, select

from tailored_kit import (
    ActorContext,
    EventEnvelope,
    InternalHttpClient,
    LangfuseClient,
    LlmClient,
    NotFoundError,
    OutboxEvent,
    OutboxRelay,
    ProcessedEvent,
    RedpandaConsumer,
    RedpandaProducer,
    RequestContext,
    ServiceSettings,
    audit_feature,
    create_service_app,
    require_internal_service,
    require_user,
)
from tailored_kit.telemetry_otel.setup import get_current_trace_context

from app.ambient import (
    evaluate_distillation_and_proactive_rules,
    update_tier0_behavior_aggregates,
)
from app.coach import _get_top_memory_facts, generate_coach_reply
from app.models import (
    AgentCheckpointDB,
    AgentMessageDB,
    AgentThreadDB,
    BehavioralMemoryFactDB,
    ProactiveSuggestionDB,
    ProposalCardDB,
    UserBehaviorProfileDB,
    utc_now,
)

logger = logging.getLogger(__name__)


class AiAgentSettings(ServiceSettings):
    service_name: str = "ai-agent-service"
    database_url: str = "postgresql+psycopg://ai_agent_svc:tailored_ai_pass@postgres:5432/ai_agent_db"
    profile_service_url: str = "http://profile-service:8002"
    jobs_service_url: str = "http://jobs-service:8003"
    documents_service_url: str = "http://documents-service:8004"
    pipeline_service_url: str = "http://pipeline-service:8005"


settings = AiAgentSettings()
engine = create_engine(settings.database_url, pool_pre_ping=True)
llm_client = LlmClient()
langfuse_client = LangfuseClient()

AI_TABLES = [
    UserBehaviorProfileDB.__table__,
    BehavioralMemoryFactDB.__table__,
    AgentThreadDB.__table__,
    AgentCheckpointDB.__table__,
    AgentMessageDB.__table__,
    ProposalCardDB.__table__,
    ProactiveSuggestionDB.__table__,
    OutboxEvent.__table__,
    ProcessedEvent.__table__,
]

ALLOWLIST_BEHAVIOR_EVENTS = {
    "ui.job.dwelled",
    "ui.jd.scrolled",
    "ui.skill_gap.clicked",
    "ui.job.saved_interest",
    "ui.job.hidden",
    "ui.persona.switched",
    "ui.studio.abandoned",
    "ui.proposal.resolved",
    "ui.studio.manual_undo_loop",
    "ui.radar.searched",
}


def _enqueue_outbox(
    session: Session,
    *,
    event_type: str,
    user_id: str,
    anon_id: Optional[str],
    feature_key: str,
    payload: Dict[str, Any],
) -> None:
    trace_id, span_id = get_current_trace_context()
    session.add(
        OutboxEvent(
            event_id=str(uuid4()),
            aggregate_type="ai_agent",
            aggregate_id=user_id,
            topic="ai.events.v1",
            event_type=event_type,
            partition_key=user_id,
            payload_json=json.dumps(payload, default=str),
            headers_json=json.dumps(
                {
                    "trace_id": trace_id,
                    "span_id": span_id,
                    "feature_key": feature_key,
                    "actor": {"user_id": user_id, "analytics_anon_id": anon_id},
                }
            ),
        )
    )


def _delete_user_ai_data(user_id: str) -> None:
    with Session(engine) as session:
        threads = session.exec(select(AgentThreadDB).where(AgentThreadDB.user_id == user_id)).all()
        for t in threads:
            session.exec(delete(ProposalCardDB).where(ProposalCardDB.thread_id == t.id))
            session.exec(delete(AgentMessageDB).where(AgentMessageDB.thread_id == t.id))
            session.exec(delete(AgentCheckpointDB).where(AgentCheckpointDB.thread_id == t.id))
        session.exec(delete(AgentThreadDB).where(AgentThreadDB.user_id == user_id))
        session.exec(delete(BehavioralMemoryFactDB).where(BehavioralMemoryFactDB.user_id == user_id))
        session.exec(delete(ProactiveSuggestionDB).where(ProactiveSuggestionDB.user_id == user_id))
        session.exec(delete(UserBehaviorProfileDB).where(UserBehaviorProfileDB.user_id == user_id))
        session.commit()


async def _is_passive_learning_allowed(redis_client: aioredis.Redis, user_id: str) -> bool:
    raw = await redis_client.get(f"consent:{user_id}")
    if not raw:
        return True
    try:
        data = json.loads(raw)
        return bool(data.get("ai_passive_learning", True))
    except Exception:
        return True


@asynccontextmanager
async def lifespan(app: FastAPI):
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.commit()
    SQLModel.metadata.create_all(engine, tables=AI_TABLES)
    try:
        with engine.connect() as conn:
            conn.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS ix_behavioral_memory_embedding_hnsw "
                    "ON behavioral_memory_facts USING hnsw (embedding vector_cosine_ops)"
                )
            )
            conn.commit()
    except Exception as exc:
        logger.warning("HNSW index creation skipped (%s)", exc)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    app.state.redis = redis_client

    producer = RedpandaProducer(settings.redpanda_brokers)
    try:
        await producer.start()
    except Exception as exc:
        logger.warning("Redpanda unavailable (%s)", exc)
    app.state.redpanda_producer = producer

    relay = OutboxRelay(
        session_factory=lambda: Session(engine),
        producer=producer,
        service_name=settings.service_name,
    )
    await relay.start()

    internal_http = InternalHttpClient(
        caller_service=settings.service_name,
        hmac_secret=settings.internal_hmac_secret,
        timeout_seconds=4.0,
    )
    app.state.internal_http = internal_http

    async def on_behavior_event(env: EventEnvelope) -> None:
        p = env.payload
        uid = p.get("user_id") or env.actor.user_id
        if env.event_type == "user.erasure.requested":
            if uid:
                _delete_user_ai_data(uid)
            return

        if not uid:
            return
        if env.event_type not in ALLOWLIST_BEHAVIOR_EVENTS and p.get("event_name") not in ALLOWLIST_BEHAVIOR_EVENTS:
            return
        if not await _is_passive_learning_allowed(redis_client, uid):
            return

        ev_name = p.get("event_name") or env.event_type
        fk = p.get("feature_key") or env.feature_key or ev_name
        persona_track = p.get("persona_track") or "unknown"

        with Session(engine) as session:
            prof = update_tier0_behavior_aggregates(
                session,
                user_id=uid,
                event_id=env.event_id,
                event_name=ev_name,
                feature_key=fk,
                persona_track=persona_track,
                payload=p,
            )
            distilled, sugg = await evaluate_distillation_and_proactive_rules(
                session,
                redis_client,
                prof=prof,
                latest_event_id=env.event_id,
                llm_client=llm_client,
            )
            if distilled:
                _enqueue_outbox(
                    session,
                    event_type="ai.memory.distilled",
                    user_id=uid,
                    anon_id=env.actor.analytics_anon_id,
                    feature_key="ai.ambient.memory_distill",
                    payload={"user_id": uid, "facts_count": len(distilled)},
                )
            if sugg:
                _enqueue_outbox(
                    session,
                    event_type="ai.suggestion.emitted",
                    user_id=uid,
                    anon_id=env.actor.analytics_anon_id,
                    feature_key="ai.ambient.nudge_emit",
                    payload=sugg,
                )
            session.commit()

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["telemetry.interactions.v1", "identity.lifecycle.v1", "pipeline.events.v1"],
        group_id="ai-behavior-cg",
        handler=on_behavior_event,
        dlq_producer=producer,
    )
    try:
        await consumer.start()
    except Exception as exc:
        logger.warning("Consumer delayed (%s)", exc)

    try:
        yield
    finally:
        await consumer.stop()
        await internal_http.close()
        await relay.stop()
        await producer.stop()
        await redis_client.aclose()


app = create_service_app(
    settings,
    title="Tailored AI Agent & Ambient Intelligence Service",
    lifespan=lifespan,
)


# --- Schemas ---

class ThreadCreateRequest(BaseModel):
    surface: str = "cv"
    scope: str = "role"
    doc_id: Optional[str] = None
    job_id: Optional[str] = None
    title: str = "Studio Coach"


class MessageStreamRequest(BaseModel):
    prompt: str
    mode: str = "Surgical"
    focused_anchor: Optional[Dict[str, str]] = None
    job_id: Optional[str] = None
    doc_id: Optional[str] = None


class BranchRequest(BaseModel):
    checkpoint_id: str
    new_prompt: str
    mode: str = "Surgical"


class ProposalResolveRequest(BaseModel):
    action: str  # apply | skip | undo | refine
    refine_instruction: Optional[str] = None


class ActionConfirmRequest(BaseModel):
    confirm: bool = True


class SuggestionResolveRequest(BaseModel):
    status: str  # clicked | dismissed


# --- Threads & Streaming Coach ---

@app.get("/api/v1/agent/threads")
async def list_threads(
    surface: Optional[str] = Query(default=None),
    ctx: RequestContext = Depends(require_user),
) -> List[Dict[str, Any]]:
    with Session(engine) as session:
        stmt = select(AgentThreadDB).where(AgentThreadDB.user_id == ctx.user_id)
        if surface:
            stmt = stmt.where(AgentThreadDB.surface == surface)
        rows = session.exec(stmt.order_by(AgentThreadDB.updated_at.desc())).all()
        return [r.model_dump() for r in rows]


@app.post("/api/v1/agent/threads", status_code=status.HTTP_201_CREATED)
async def create_thread(
    payload: ThreadCreateRequest, ctx: RequestContext = Depends(require_user)
) -> Dict[str, Any]:
    with Session(engine) as session:
        t = AgentThreadDB(
            user_id=ctx.user_id,
            surface=payload.surface,
            scope=payload.scope,
            doc_id=payload.doc_id,
            job_id=payload.job_id,
            title=payload.title,
        )
        session.add(t)
        session.flush()
        cp = AgentCheckpointDB(thread_id=t.id, state_json=json.dumps({"turn": 0}))
        session.add(cp)
        session.flush()
        t.active_checkpoint_id = cp.id
        session.add(t)
        session.commit()
        session.refresh(t)
        return t.model_dump()


@app.get("/api/v1/agent/threads/{thread_id}")
async def get_thread(thread_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        t = session.get(AgentThreadDB, thread_id)
        if not t or t.user_id != ctx.user_id:
            raise NotFoundError("Thread not found.")
        msgs = session.exec(
            select(AgentMessageDB)
            .where(AgentMessageDB.thread_id == t.id)
            .order_by(AgentMessageDB.created_at.asc())
        ).all()
        proposals = {
            p.message_id: p.model_dump()
            for p in session.exec(select(ProposalCardDB).where(ProposalCardDB.thread_id == t.id)).all()
        }
        formatted_msgs = []
        for m in msgs:
            d = m.model_dump()
            if m.id in proposals:
                d["proposal"] = proposals[m.id]
            formatted_msgs.append(d)
        return {"thread": t.model_dump(), "messages": formatted_msgs}


async def _run_coach_turn_and_stream(
    *,
    request: Request,
    ctx: RequestContext,
    thread_id: str,
    prompt: str,
    mode: str,
    focused_anchor: Optional[Dict[str, str]],
    job_id: Optional[str],
    doc_id: Optional[str],
    parent_checkpoint_id: Optional[str] = None,
):
    client: InternalHttpClient = request.app.state.internal_http
    trace_id, _ = get_current_trace_context()

    with Session(engine) as session:
        thread = session.get(AgentThreadDB, thread_id)
        if not thread or thread.user_id != ctx.user_id:
            raise NotFoundError("Thread not found.")

        eff_job_id = job_id or thread.job_id
        eff_doc_id = doc_id or thread.doc_id
        parent_cp = parent_checkpoint_id or thread.active_checkpoint_id
        cp = AgentCheckpointDB(
            thread_id=thread.id,
            parent_checkpoint_id=parent_cp,
            state_json=json.dumps({"prompt": prompt, "mode": mode}),
        )
        session.add(cp)
        session.flush()
        cp_id = cp.id

        prior_msgs = session.exec(
            select(AgentMessageDB)
            .where(AgentMessageDB.thread_id == thread.id, AgentMessageDB.role == "user")
            .order_by(AgentMessageDB.created_at.asc())
        ).all()
        prior_user_texts = [m.content_text for m in prior_msgs]
        memory_facts = await _get_top_memory_facts(
            session,
            ctx.user_id,
            prompt,
            llm_client=llm_client,
        )

        user_msg = AgentMessageDB(
            thread_id=thread.id,
            checkpoint_id=cp_id,
            role="user",
            content_text=prompt,
            focused_anchor_json=json.dumps(focused_anchor) if focused_anchor else None,
        )
        session.add(user_msg)
        thread.active_checkpoint_id = cp_id
        thread.updated_at = utc_now()
        session.add(thread)
        surface = thread.surface
        session.commit()

    # Assemble cross-service context asynchronously
    prof_summary: Dict[str, Any] = {}
    job_ctx: Dict[str, Any] = {}
    try:
        pr = await client.get(f"{settings.profile_service_url}/internal/profiles/{ctx.user_id}/summary")
        if pr.status_code == 200:
            prof_summary = pr.json()
    except Exception:
        pass
    if eff_job_id:
        try:
            jr = await client.get(
                f"{settings.jobs_service_url}/internal/jobs/{eff_job_id}/fit-context",
                params={"user_id": ctx.user_id},
            )
            if jr.status_code == 200:
                job_ctx = jr.json()
        except Exception:
            pass

    reply = await generate_coach_reply(
        prompt=prompt,
        surface=surface,
        mode=mode,
        profile_summary=prof_summary,
        job_ctx=job_ctx,
        prior_user_texts=prior_user_texts,
        memory_facts=memory_facts,
        focused_anchor=focused_anchor,
        llm_client=llm_client,
    )

    if trace_id:
        await langfuse_client.record_trace(
            trace_id=trace_id,
            name=f"coach.{surface}",
            user_id=ctx.user_id,
            input_data={"prompt": prompt, "mode": mode, "surface": surface},
            output_data={
                "text": reply.get("text"),
                "has_proposal": bool(reply.get("proposal")),
                "has_action_card": bool(reply.get("action_card")),
            },
            metadata={"thread_id": thread_id, "job_id": eff_job_id, "doc_id": eff_doc_id},
        )

    with Session(engine) as session:
        assistant_msg = AgentMessageDB(
            thread_id=thread_id,
            checkpoint_id=cp_id,
            role="assistant",
            content_text=reply["text"],
            thinking_summary=reply.get("thinking_summary"),
            resources_json=json.dumps(reply["resources"]) if reply.get("resources") else None,
            action_card_json=json.dumps(reply["action_card"]) if reply.get("action_card") else None,
            audit_json=json.dumps(reply["audit"]) if reply.get("audit") else None,
            langfuse_trace_id=trace_id,
        )
        session.add(assistant_msg)
        session.flush()

        proposal_dict = None
        if reply.get("proposal"):
            pr_in = reply["proposal"]
            pcard = ProposalCardDB(
                thread_id=thread_id,
                message_id=assistant_msg.id,
                user_id=ctx.user_id,
                doc_id=eff_doc_id,
                target_anchor_id=pr_in["targetAnchorId"],
                target_label=pr_in["targetLabel"],
                old_text=pr_in["oldText"],
                new_text=pr_in["newText"],
                is_metric_question=bool(pr_in.get("isMetricQuestion")),
            )
            session.add(pcard)
            session.flush()
            proposal_dict = {
                "id": pcard.id,
                "targetAnchorId": pcard.target_anchor_id,
                "targetLabel": pcard.target_label,
                "oldText": pcard.old_text,
                "newText": pcard.new_text,
                "status": pcard.status,
                "isMetricQuestion": pcard.is_metric_question,
            }
            if pcard.is_metric_question:
                _enqueue_outbox(
                    session,
                    event_type="ai.metric.intercepted",
                    user_id=ctx.user_id,
                    anon_id=ctx.analytics_anon_id,
                    feature_key="ai.studio.metric_guard",
                    payload={"user_id": ctx.user_id, "proposal_id": pcard.id, "thread_id": thread_id},
                )

        action_dict = None
        if reply.get("action_card"):
            ac = dict(reply["action_card"])
            ac["id"] = f"act_{assistant_msg.id[:12]}"
            assistant_msg.action_card_json = json.dumps(ac)
            session.add(assistant_msg)
            action_dict = ac

        session.commit()
        msg_id = assistant_msg.id

    async def sse_gen():
        if reply.get("thinking_summary"):
            yield f"event: thinking_step\ndata: {json.dumps({'step': reply['thinking_summary']})}\n\n"
            await asyncio.sleep(0.02)
        yield f"event: text_delta\ndata: {json.dumps({'delta': reply['text']})}\n\n"
        if proposal_dict:
            yield f"event: proposal_card\ndata: {json.dumps(proposal_dict)}\n\n"
        if action_dict:
            yield f"event: action_card\ndata: {json.dumps(action_dict)}\n\n"
        if reply.get("resources"):
            yield f"event: resource_list\ndata: {json.dumps(reply['resources'])}\n\n"
        if reply.get("audit"):
            yield f"event: audit_summary\ndata: {json.dumps(reply['audit'])}\n\n"
        yield f"event: done\ndata: {json.dumps({'message_id': msg_id, 'checkpoint_id': cp_id, 'langfuse_trace_id': trace_id})}\n\n"

    return StreamingResponse(
        sse_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/api/v1/agent/threads/{thread_id}/messages:stream")
@audit_feature(feature_key="ai.coach.chat_turn", resource_type="agent_message", action="stream_turn")
async def stream_coach_message(
    thread_id: str,
    payload: MessageStreamRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
):
    return await _run_coach_turn_and_stream(
        request=request,
        ctx=ctx,
        thread_id=thread_id,
        prompt=payload.prompt,
        mode=payload.mode,
        focused_anchor=payload.focused_anchor,
        job_id=payload.job_id,
        doc_id=payload.doc_id,
    )


@app.post("/api/v1/agent/threads/{thread_id}/branch")
async def branch_thread(
    thread_id: str,
    payload: BranchRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
):
    return await _run_coach_turn_and_stream(
        request=request,
        ctx=ctx,
        thread_id=thread_id,
        prompt=payload.new_prompt,
        mode=payload.mode,
        focused_anchor=None,
        job_id=None,
        doc_id=None,
        parent_checkpoint_id=payload.checkpoint_id,
    )


@app.post("/api/v1/agent/proposals/{proposal_id}/resolve")
@audit_feature(feature_key="ai.coach.proposal.resolve", resource_type="proposal_card", action="resolve")
async def resolve_proposal(
    proposal_id: str,
    payload: ProposalResolveRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    action = payload.action.lower()
    with Session(engine) as session:
        card = session.get(ProposalCardDB, proposal_id)
        if not card or card.user_id != ctx.user_id:
            raise NotFoundError("Proposal card not found.")

        if action == "refine":
            card.refine_count += 1
            card.new_text = f"{card.new_text} ({payload.refine_instruction or 'concise'})"
        elif action in ("apply", "applied"):
            card.status = "applied"
            card.resolved_at = utc_now()
            if card.doc_id:
                try:
                    await client.patch(
                        f"{settings.documents_service_url}/internal/documents/{card.doc_id}/apply-proposal",
                        json={
                            "user_id": ctx.user_id,
                            "old_text": card.old_text,
                            "new_text": card.new_text,
                            "proposal_card_id": card.id,
                        },
                    )
                except Exception as exc:
                    logger.warning("Doc apply patch failed (%s)", exc)
        elif action in ("skip", "skipped"):
            card.status = "skipped"
            card.resolved_at = utc_now()
        elif action in ("undo", "undone"):
            card.status = "undone"
            card.resolved_at = utc_now()

        score_map = {"applied": 1.0, "skipped": 0.0, "undone": -1.0, "pending": 0.5}
        eval_score = score_map.get(card.status, 0.5)
        msg_obj = session.get(AgentMessageDB, card.message_id)
        trace_id_for_score = (msg_obj.langfuse_trace_id if msg_obj else None) or get_current_trace_context()[0]
        session.add(card)
        _enqueue_outbox(
            session,
            event_type="ai.proposal.resolved",
            user_id=ctx.user_id,
            anon_id=ctx.analytics_anon_id,
            feature_key="ai.coach.proposal.resolve",
            payload={
                "user_id": ctx.user_id,
                "proposal_id": card.id,
                "resolution": card.status,
                "eval_score": eval_score,
            },
        )
        session.commit()
        session.refresh(card)
        out_card = card.model_dump()

    if trace_id_for_score:
        await langfuse_client.record_score(
            trace_id=trace_id_for_score,
            name="proposal_resolution",
            value=eval_score,
            comment=f"action={action},status={out_card['status']}",
        )
    return {"proposal": out_card, "langfuse_eval_score": eval_score}


@app.post("/api/v1/agent/actions/{action_id}/confirm")
@audit_feature(feature_key="ai.coach.action.confirm", resource_type="action_card", action="confirm")
async def confirm_action_card(
    action_id: str,
    payload: ActionConfirmRequest,
    request: Request,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    client: InternalHttpClient = request.app.state.internal_http
    msg_prefix = action_id.replace("act_", "")
    with Session(engine) as session:
        msg = session.exec(
            select(AgentMessageDB).where(AgentMessageDB.id.startswith(msg_prefix))
        ).first()
        if not msg or not msg.action_card_json:
            raise NotFoundError("Action card not found.")
        ac = json.loads(msg.action_card_json)
        if not payload.confirm:
            ac["status"] = "cancelled"
            msg.action_card_json = json.dumps(ac)
            session.add(msg)
            session.commit()
            return {"status": "cancelled", "action_card": ac}

        p = ac.get("payload") or {}
        if ac.get("actionType") == "pipeline_stage" and p.get("jobId"):
            await client.patch(
                f"{settings.pipeline_service_url}/internal/pipeline/by-job/{p['jobId']}",
                json={
                    "user_id": ctx.user_id,
                    "status": p.get("status", "applied"),
                    "company_name": p.get("company_name", ""),
                    "job_title": p.get("job_title", ""),
                },
            )
        ac["status"] = "confirmed"
        msg.action_card_json = json.dumps(ac)
        session.add(msg)
        session.commit()
        return {"status": "confirmed", "action_card": ac}


# --- AI Behavioral Memory Inspector & Proactive Suggestions ---

@app.get("/api/v1/agent/memory")
async def get_ai_memory(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        prof = session.get(UserBehaviorProfileDB, ctx.user_id)
        facts = session.exec(
            select(BehavioralMemoryFactDB)
            .where(
                BehavioralMemoryFactDB.user_id == ctx.user_id,
                BehavioralMemoryFactDB.status == "active",
            )
            .order_by(BehavioralMemoryFactDB.last_reinforced_at.desc())
        ).all()
        suggestions = session.exec(
            select(ProactiveSuggestionDB)
            .where(ProactiveSuggestionDB.user_id == ctx.user_id)
            .order_by(ProactiveSuggestionDB.created_at.desc())
        ).all()
        return {
            "behavior_profile": prof.model_dump() if prof else None,
            "memory_facts": [
                {
                    "id": f.id,
                    "category": f.category,
                    "fact_text": f.fact_text,
                    "confidence": f.confidence,
                    "source_event_ids": json.loads(f.source_event_ids_json or "[]"),
                    "last_reinforced_at": f.last_reinforced_at.isoformat(),
                }
                for f in facts
            ],
            "proactive_suggestions": [s.model_dump() for s in suggestions],
        }


@app.delete("/api/v1/agent/memory/{fact_id}")
async def delete_memory_fact(fact_id: str, ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        fact = session.get(BehavioralMemoryFactDB, fact_id)
        if not fact or fact.user_id != ctx.user_id:
            raise NotFoundError("Memory fact not found.")
        fact.status = "dismissed_by_user"
        session.add(fact)
        session.commit()
        return {"deleted": fact_id}


@app.delete("/api/v1/agent/memory")
async def clear_all_memory(ctx: RequestContext = Depends(require_user)) -> Dict[str, Any]:
    with Session(engine) as session:
        session.exec(delete(BehavioralMemoryFactDB).where(BehavioralMemoryFactDB.user_id == ctx.user_id))
        session.exec(delete(ProactiveSuggestionDB).where(ProactiveSuggestionDB.user_id == ctx.user_id))
        session.exec(delete(UserBehaviorProfileDB).where(UserBehaviorProfileDB.user_id == ctx.user_id))
        session.commit()
        return {"cleared": True}


@app.post("/api/v1/agent/suggestions/{suggestion_id}/resolve")
async def resolve_suggestion(
    suggestion_id: str,
    payload: SuggestionResolveRequest,
    ctx: RequestContext = Depends(require_user),
) -> Dict[str, Any]:
    with Session(engine) as session:
        s = session.get(ProactiveSuggestionDB, suggestion_id)
        if not s or s.user_id != ctx.user_id:
            raise NotFoundError("Suggestion not found.")
        s.status = payload.status
        s.resolved_at = utc_now()
        session.add(s)
        session.commit()
        return s.model_dump()
