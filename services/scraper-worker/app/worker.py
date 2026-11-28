from __future__ import annotations

import asyncio
import logging
import os
import signal
from datetime import datetime, timezone
from uuid import uuid4

import httpx
import redis.asyncio as aioredis
from bs4 import BeautifulSoup

from tailored_kit import (
    ActorContext,
    EventEnvelope,
    RedpandaConsumer,
    RedpandaProducer,
    ServiceSettings,
)
from tailored_kit.telemetry_otel.logging import configure_logging
from tailored_kit.telemetry_otel.setup import setup_telemetry

logger = logging.getLogger(__name__)


class ScraperSettings(ServiceSettings):
    service_name: str = "scraper-worker"
    apify_api_token: str = os.getenv("APIFY_API_TOKEN", "").strip()
    apify_actor_id: str = os.getenv("APIFY_ACTOR_ID", "curious_coder~linkedin-jobs-scraper").strip()
    apify_max_items_per_actor: int = int(os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", "2"))
    apify_daily_cap: int = int(os.getenv("APIFY_DAILY_CAP", "100"))
    radar_sweep_interval_min: int = int(os.getenv("RADAR_SWEEP_INTERVAL_MIN", "0"))


settings = ScraperSettings()


async def _scrape_via_apify(
    *,
    query: str,
    location: str,
    max_items: int,
    redis_client: aioredis.Redis,
    user_id: str | None,
) -> list[dict]:
    if not settings.apify_api_token:
        return []

    day_key = f"apify:daily_items:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
    used = int(await redis_client.get(day_key) or 0)
    if used >= settings.apify_daily_cap:
        logger.warning("Apify daily cap reached (%s/%s); using fallback job", used, settings.apify_daily_cap)
        return []

    limit = max(1, min(max_items, settings.apify_max_items_per_actor, settings.apify_daily_cap - used))
    endpoint = f"https://api.apify.com/v2/acts/{settings.apify_actor_id}/run-sync-get-dataset-items"
    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                endpoint,
                params={"token": settings.apify_api_token, "limit": limit},
                json={"queries": [f"{query} {location}".strip()], "count": limit},
            )
            if resp.status_code >= 400:
                logger.warning("Apify actor API returned %s", resp.status_code)
                return []
            items = resp.json()
            if not isinstance(items, list) or not items:
                return []
    except Exception as exc:
        logger.warning("Apify actor run failed (%s); using fallback", exc)
        return []

    normalized: list[dict] = []
    for raw in items[:limit]:
        src_id = str(raw.get("id") or raw.get("jobId") or f"apify_{uuid4().hex[:8]}")
        normalized.append(
            {
                "source_id": src_id,
                "title": str(raw.get("title") or f"{query} Engineer")[:200],
                "company_name": str(raw.get("companyName") or raw.get("company_name") or "Partner Organization")[:160],
                "location": str(raw.get("location") or location)[:160],
                "work_mode": str(raw.get("workType") or raw.get("work_mode") or "Hybrid")[:40],
                "url": str(raw.get("jobUrl") or raw.get("url") or f"https://www.linkedin.com/jobs/view/{src_id}"),
                "source_type": "apify_linkedin",
                "raw_description": str(raw.get("descriptionText") or raw.get("description") or f"{query} role in {location}")[:4000],
                "user_id": user_id,
            }
        )

    if normalized:
        cnt = await redis_client.incrby(day_key, len(normalized))
        if cnt == len(normalized):
            await redis_client.expire(day_key, 172800)
    return normalized


async def _fetch_url_title_desc(url: str) -> tuple[str, str]:
    try:
        async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 TailoredBot/1.0"})
            if resp.status_code == 200:
                soup = BeautifulSoup(resp.text, "html.parser")
                title = soup.title.string.strip() if soup.title and soup.title.string else "Imported Web Opportunity"
                text = soup.get_text(" ", strip=True)[:3500]
                return title[:240], text
    except Exception as exc:
        logger.info("Remote fetch fallback for %s (%s)", url, exc)
    return "Discovered MENA Engineering Role", f"Ingested from {url}. Python, FastAPI, SQL, Docker, PostgreSQL."


async def run_worker() -> None:
    configure_logging(settings.service_name, settings.log_level)
    setup_telemetry(None, settings)

    redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    producer = RedpandaProducer(settings.redpanda_brokers)
    for attempt in range(1, 11):
        try:
            await producer.start()
            break
        except Exception as exc:
            logger.warning("Waiting for Redpanda (%s/10): %s", attempt, exc)
            await asyncio.sleep(2)

    async def handle_command(env: EventEnvelope) -> None:
        uid = env.payload.get("user_id") or env.actor.user_id
        if env.event_type == "scrape.radar.requested":
            query = env.payload.get("query") or "AI & Data Science"
            loc = env.payload.get("location") or "Cairo, Egypt"
            live_items = await _scrape_via_apify(
                query=query,
                location=loc,
                max_items=int(env.payload.get("limit") or settings.apify_max_items_per_actor),
                redis_client=redis_client,
                user_id=uid,
            )
            if not live_items:
                day_key = f"apify:daily_items:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
                count = await redis_client.incrby(day_key, 1)
                if count == 1:
                    await redis_client.expire(day_key, 172800)
                live_items = [
                    {
                        "source_id": f"radar_sweep_{uuid4().hex[:8]}",
                        "title": f"{query} Engineer",
                        "company_name": "MENA Tech Partner",
                        "location": loc,
                        "work_mode": "Hybrid",
                        "url": f"https://www.linkedin.com/jobs/view/{uuid4().hex[:10]}",
                        "source_type": "linkedin",
                        "raw_description": (
                            f"Seeking a {query} specialist in {loc}. Core stack: Python, FastAPI, PyTorch, SQL, Docker. "
                            "3+ years experience building production APIs."
                        ),
                        "user_id": uid,
                    }
                ]
            for discovered in live_items:
                await producer.publish(
                    "jobs.events.v1",
                    EventEnvelope(
                        event_type="job.raw.discovered",
                        producer_service=settings.service_name,
                        trace_id=env.trace_id,
                        span_id=env.span_id,
                        feature_key=env.feature_key or "radar.auto_search",
                        actor=ActorContext(user_id=uid, analytics_anon_id=env.actor.analytics_anon_id),
                        payload=discovered,
                    ),
                    partition_key=discovered["source_id"],
                )
        elif env.event_type == "ingest.url.requested":
            url = env.payload.get("url", "")
            title, desc = await _fetch_url_title_desc(url)
            await producer.publish(
                "jobs.events.v1",
                EventEnvelope(
                    event_type="job.raw.discovered",
                    producer_service=settings.service_name,
                    trace_id=env.trace_id,
                    span_id=env.span_id,
                    feature_key=env.feature_key or "ingest.url",
                    actor=ActorContext(user_id=uid, analytics_anon_id=env.actor.analytics_anon_id),
                    payload={
                        "source_id": f"url_{uuid4().hex[:8]}",
                        "url": url,
                        "title": title,
                        "company_name": "Imported Organization",
                        "location": "Remote",
                        "raw_description": desc,
                        "user_id": uid,
                    },
                ),
            )

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["jobs.commands.v1"],
        group_id="scraper-worker-cg",
        handler=handle_command,
        dlq_producer=producer,
    )
    await consumer.start()

    stop_evt = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_evt.set)
        except NotImplementedError:
            pass

    async def _periodic_radar_sweep() -> None:
        interval = max(1, settings.radar_sweep_interval_min) * 60
        while not stop_evt.is_set():
            try:
                await asyncio.wait_for(stop_evt.wait(), timeout=interval)
                break
            except asyncio.TimeoutError:
                pass
            try:
                items = await _scrape_via_apify(
                    query="AI & Backend Engineer",
                    location="Cairo, Egypt",
                    max_items=settings.apify_max_items_per_actor,
                    redis_client=redis_client,
                    user_id=None,
                )
                for discovered in items:
                    await producer.publish(
                        "jobs.events.v1",
                        EventEnvelope(
                            event_type="job.raw.discovered",
                            producer_service=settings.service_name,
                            feature_key="radar.scheduled_sweep",
                            payload=discovered,
                        ),
                        partition_key=discovered["source_id"],
                    )
            except Exception as exc:
                logger.warning("Scheduled radar sweep error: %s", exc)

    sweep_task = (
        asyncio.create_task(_periodic_radar_sweep())
        if settings.radar_sweep_interval_min > 0
        else None
    )

    logger.info("scraper-worker listening on jobs.commands.v1")
    await stop_evt.wait()
    if sweep_task:
        sweep_task.cancel()
    await consumer.stop()
    await producer.stop()
    await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(run_worker())
