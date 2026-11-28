from __future__ import annotations

import asyncio
import logging
import signal
import tempfile
from pathlib import Path
from typing import Optional

import boto3
from botocore.client import Config as BotoConfig

from tailored_kit import (
    ActorContext,
    EventEnvelope,
    RedpandaConsumer,
    RedpandaProducer,
    ServiceSettings,
)
from tailored_kit.telemetry_otel.logging import configure_logging
from tailored_kit.telemetry_otel.setup import setup_telemetry

from app.latex_engine import compile_latex, sanitize_latex_content, unwrap_paragraph_text_macros

logger = logging.getLogger(__name__)


class LatexWorkerSettings(ServiceSettings):
    service_name: str = "latex-worker"
    minio_endpoint: str = "http://minio:9000"
    minio_root_user: str = "tailored_minio"
    minio_root_password: str = "tailored_minio_dev_pass"


settings = LatexWorkerSettings()


def _s3_client():
    return boto3.client(
        "s3",
        endpoint_url=settings.minio_endpoint,
        aws_access_key_id=settings.minio_root_user,
        aws_secret_access_key=settings.minio_root_password,
        config=BotoConfig(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _compile_and_upload(
    *,
    user_id: str,
    doc_id: str,
    version_no: int,
    latex_content: str,
) -> tuple[bool, Optional[str], Optional[str], str]:
    # Chaos / test hook for verifying automatic credit refund on compile failure
    if "\\FAIL_COMPILE_TEST" in (latex_content or "") or not (latex_content or "").strip():
        return False, None, None, "Simulated LaTeX compile failure triggered."

    sanitized = unwrap_paragraph_text_macros(sanitize_latex_content(latex_content))
    with tempfile.TemporaryDirectory(prefix=f"latex_{doc_id}_") as tmp_dir:
        folder = Path(tmp_dir)
        tex_path = folder / "cv.tex"
        pdf_path = folder / "cv.pdf"
        tex_path.write_text(sanitized, encoding="utf-8")

        status_str, _notes, errors = compile_latex(folder)
        if status_str != "ok" or not pdf_path.exists():
            return False, None, None, "; ".join(errors) or "Compilation produced no PDF."

        s3 = _s3_client()
        tex_key = f"{user_id}/{doc_id}/v{version_no}/cv.tex"
        pdf_key = f"{user_id}/{doc_id}/v{version_no}/cv.pdf"
        s3.put_object(Bucket="cv-artifacts", Key=tex_key, Body=tex_path.read_bytes(), ContentType="text/x-tex")
        s3.put_object(Bucket="cv-artifacts", Key=pdf_key, Body=pdf_path.read_bytes(), ContentType="application/pdf")
        return True, tex_key, pdf_key, ""


async def run_worker() -> None:
    configure_logging(settings.service_name, settings.log_level)
    setup_telemetry(None, settings)

    producer = RedpandaProducer(settings.redpanda_brokers)
    for attempt in range(1, 11):
        try:
            await producer.start()
            break
        except Exception as exc:
            logger.warning("Waiting for Redpanda (%s/10): %s", attempt, exc)
            await asyncio.sleep(2)

    async def handle_command(env: EventEnvelope) -> None:
        if env.event_type != "latex.compile.requested":
            return
        p = env.payload
        uid = p.get("user_id") or env.actor.user_id or "anonymous"
        doc_id = p["doc_id"]
        version_no = int(p.get("version_no") or 1)
        hold_id = p.get("credit_hold_id")
        latex = p.get("latex_content") or ""

        ok, tex_key, pdf_key, err_msg = await asyncio.to_thread(
            _compile_and_upload,
            user_id=uid,
            doc_id=doc_id,
            version_no=version_no,
            latex_content=latex,
        )
        out_type = "latex.compile.succeeded" if ok else "latex.compile.failed"
        await producer.publish(
            "documents.events.v1",
            EventEnvelope(
                event_type=out_type,
                producer_service=settings.service_name,
                trace_id=env.trace_id,
                span_id=env.span_id,
                feature_key=env.feature_key or "studio.cv.compile",
                idempotency_key=f"{doc_id}_v{version_no}_{out_type}",
                actor=ActorContext(user_id=uid, analytics_anon_id=env.actor.analytics_anon_id),
                payload={
                    "user_id": uid,
                    "doc_id": doc_id,
                    "version_no": version_no,
                    "credit_hold_id": hold_id,
                    "tex_object_key": tex_key,
                    "pdf_object_key": pdf_key,
                    "error_message": err_msg,
                },
            ),
            partition_key=uid,
        )

    consumer = RedpandaConsumer(
        brokers=settings.redpanda_brokers,
        topics=["documents.commands.v1"],
        group_id="latex-worker-cg",
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

    logger.info("latex-worker sandbox listening on documents.commands.v1")
    await stop_evt.wait()
    await consumer.stop()
    await producer.stop()


if __name__ == "__main__":
    asyncio.run(run_worker())
