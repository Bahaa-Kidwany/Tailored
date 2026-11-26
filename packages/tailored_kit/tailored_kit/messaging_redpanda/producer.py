import logging
from typing import Dict, Optional

from aiokafka import AIOKafkaProducer

from tailored_kit.messaging_redpanda.envelope import EventEnvelope, inject_trace_headers

logger = logging.getLogger(__name__)


class RedpandaProducer:
    """Async Kafka/Redpanda producer with idempotence, acks=all, and W3C trace headers."""

    def __init__(self, brokers: str) -> None:
        self.brokers = brokers
        self._producer: Optional[AIOKafkaProducer] = None

    async def start(self) -> None:
        if self._producer is not None:
            return
        self._producer = AIOKafkaProducer(
            bootstrap_servers=self.brokers,
            acks="all",
            enable_idempotence=True,
            value_serializer=lambda v: v.encode("utf-8") if isinstance(v, str) else v,
            key_serializer=lambda k: k.encode("utf-8") if isinstance(k, str) else k,
        )
        await self._producer.start()
        logger.info("RedpandaProducer connected to %s", self.brokers)

    async def stop(self) -> None:
        if self._producer is not None:
            await self._producer.stop()
            self._producer = None

    @property
    def is_ready(self) -> bool:
        return self._producer is not None

    async def publish(
        self,
        topic: str,
        envelope: EventEnvelope,
        *,
        partition_key: Optional[str] = None,
        extra_headers: Optional[Dict[str, str]] = None,
    ) -> None:
        if self._producer is None:
            raise RuntimeError("RedpandaProducer has not been started.")

        headers_dict: Dict[str, str] = {
            "event_type": envelope.event_type,
            "schema_version": envelope.schema_version,
        }
        if envelope.feature_key:
            headers_dict["X-Feature-Key"] = envelope.feature_key
        if extra_headers:
            headers_dict.update(extra_headers)

        kafka_headers = inject_trace_headers(headers_dict)
        key = partition_key or envelope.actor.user_id or envelope.event_id
        await self._producer.send_and_wait(
            topic=topic,
            key=key,
            value=envelope.model_dump_json(),
            headers=kafka_headers,
        )
