import asyncio
import logging
from typing import Awaitable, Callable, Iterable, Optional

from aiokafka import AIOKafkaConsumer
from opentelemetry import trace

from tailored_kit.messaging_redpanda.envelope import EventEnvelope, extract_trace_context
from tailored_kit.messaging_redpanda.producer import RedpandaProducer

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

EventHandler = Callable[[EventEnvelope], Awaitable[None]]


class RedpandaConsumer:
    """Resilient Redpanda consumer extracting W3C trace contexts with retry backoff and DLQ routing."""

    def __init__(
        self,
        *,
        brokers: str,
        topics: Iterable[str],
        group_id: str,
        handler: EventHandler,
        dlq_producer: Optional[RedpandaProducer] = None,
        max_retries: int = 3,
    ) -> None:
        self.brokers = brokers
        self.topics = list(topics)
        self.group_id = group_id
        self.handler = handler
        self.dlq_producer = dlq_producer
        self.max_retries = max_retries
        self._consumer: Optional[AIOKafkaConsumer] = None
        self._task: Optional[asyncio.Task] = None
        self._stopping = False

    async def start(self) -> None:
        self._stopping = False
        self._consumer = AIOKafkaConsumer(
            *self.topics,
            bootstrap_servers=self.brokers,
            group_id=self.group_id,
            enable_auto_commit=False,
            auto_offset_reset="earliest",
        )
        await self._consumer.start()
        self._task = asyncio.create_task(self._run_loop(), name=f"rp-consumer-{self.group_id}")
        logger.info("RedpandaConsumer started for topics=%s group=%s", self.topics, self.group_id)

    async def stop(self) -> None:
        self._stopping = True
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        if self._consumer:
            await self._consumer.stop()
            self._consumer = None

    async def _run_loop(self) -> None:
        assert self._consumer is not None
        try:
            async for msg in self._consumer:
                if self._stopping:
                    break
                parent_ctx = extract_trace_context(msg.headers)
                raw = msg.value.decode("utf-8", errors="replace") if isinstance(msg.value, (bytes, bytearray)) else str(msg.value)
                envelope: Optional[EventEnvelope] = None
                try:
                    envelope = EventEnvelope.model_validate_json(raw)
                except Exception as exc:
                    logger.error("Invalid EventEnvelope on %s: %s", msg.topic, exc)
                    await self._consumer.commit()
                    continue

                with tracer.start_as_current_span(
                    f"redpanda.consume:{envelope.event_type}",
                    context=parent_ctx,
                ) as span:
                    span.set_attribute("messaging.system", "kafka")
                    span.set_attribute("messaging.destination.name", msg.topic)
                    if envelope.feature_key:
                        span.set_attribute("tailored.feature_key", envelope.feature_key)

                    ok = await self._execute_with_retries(envelope)
                    if not ok and self.dlq_producer and self.dlq_producer.is_ready:
                        await self._send_to_dlq(msg.topic, envelope)

                await self._consumer.commit()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.exception("RedpandaConsumer loop crashed (%s)", exc)

    async def _execute_with_retries(self, envelope: EventEnvelope) -> bool:
        for attempt in range(1, self.max_retries + 1):
            try:
                await self.handler(envelope)
                return True
            except Exception as exc:
                logger.warning(
                    "Handler failed for event_id=%s attempt=%s/%s: %s",
                    envelope.event_id,
                    attempt,
                    self.max_retries,
                    exc,
                )
                if attempt < self.max_retries:
                    await asyncio.sleep(min(2 ** (attempt - 1), 8))
        return False

    async def _send_to_dlq(self, source_topic: str, envelope: EventEnvelope) -> None:
        assert self.dlq_producer is not None
        dlq_topic = f"{source_topic}.dlq"
        try:
            await self.dlq_producer.publish(dlq_topic, envelope)
            logger.error("Routed event_id=%s to DLQ %s", envelope.event_id, dlq_topic)
        except Exception as exc:
            logger.exception("Failed publishing event_id=%s to DLQ %s: %s", envelope.event_id, dlq_topic, exc)
