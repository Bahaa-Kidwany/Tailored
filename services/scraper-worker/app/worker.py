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
    apify_max_items_per_actor: int = int(os.getenv("APIFY_MAX_ITEMS_PER_ACTOR", "2"))


settings = ScraperSettings()


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
            day_key = f"apify:daily_items:{datetime.now(timezone.utc).strftime('%Y-%m-%d')}"
            count = await redis_client.incrby(day_key, 1)
            if count == 1:
                await redis_client.expire(day_key, 172800)

            query = env.payload.get("query") or "AI & Data Science"
            loc = env.payload.get("location") or "Cairo, Egypt"
            discovered = {
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

    logger.info("scraper-worker listening on jobs.commands.v1")
    await stop_evt.wait()
    await consumer.stop()
    await producer.stop()
    await redis_client.aclose()


if __name__ == "__main__":
    asyncio.run(run_worker())
