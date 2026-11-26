import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Callable, Optional

from sqlalchemy.orm import Session
from sqlmodel import select

from tailored_kit.messaging_redpanda.envelope import ActorContext, EventEnvelope
from tailored_kit.messaging_redpanda.producer import RedpandaProducer
from tailored_kit.outbox.model import OutboxEvent

logger = logging.getLogger(__name__)


class OutboxRelay:
    """Polls unpublished OutboxEvent rows with SKIP LOCKED and dispatches them to Redpanda."""

    def __init__(
        self,
        *,
        session_factory: Callable[[], Session],
        producer: RedpandaProducer,
        service_name: str,
        poll_interval_seconds: float = 0.25,
        batch_size: int = 100,
    ) -> None:
        self.session_factory = session_factory
        self.producer = producer
        self.service_name = service_name
        self.poll_interval_seconds = poll_interval_seconds
        self.batch_size = batch_size
        self._task: Optional[asyncio.Task] = None
        self._stopping = False

    async def start(self) -> None:
        self._stopping = False
        self._task = asyncio.create_task(self._run(), name=f"outbox-relay-{self.service_name}")

    async def stop(self) -> None:
        self._stopping = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _run(self) -> None:
        while not self._stopping:
            try:
                dispatched = await self.flush_once()
                if dispatched == 0:
                    await asyncio.sleep(self.poll_interval_seconds)
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning("OutboxRelay poll error: %s", exc)
                await asyncio.sleep(1.0)

    async def flush_once(self) -> int:
        if not self.producer.is_ready:
            return 0
        count = 0
        with self.session_factory() as session:
            stmt = (
                select(OutboxEvent)
                .where(OutboxEvent.published_at.is_(None))
                .order_by(OutboxEvent.created_at)
                .limit(self.batch_size)
                .with_for_update(skip_locked=True)
            )
            rows = list(session.execute(stmt).scalars().all())
            for row in rows:
                payload = json.loads(row.payload_json) if isinstance(row.payload_json, str) else row.payload_json
                headers = json.loads(row.headers_json) if isinstance(row.headers_json, str) else row.headers_json
                envelope = EventEnvelope(
                    event_id=row.event_id,
                    event_type=row.event_type,
                    producer_service=self.service_name,
                    trace_id=headers.get("trace_id", "0" * 32),
                    span_id=headers.get("span_id", "0" * 16),
                    feature_key=headers.get("feature_key"),
                    idempotency_key=headers.get("idempotency_key", row.event_id),
                    actor=ActorContext(**headers.get("actor", {})),
                    payload=payload,
                )
                try:
                    await self.producer.publish(
                        row.topic,
                        envelope,
                        partition_key=row.partition_key,
                    )
                    row.published_at = datetime.now(timezone.utc)
                    count += 1
                except Exception as exc:
                    row.retry_count += 1
                    row.last_error = str(exc)[:500]
            session.commit()
        return count
