"""`POST /webhooks/github` — deliberately outside `/api/v1` (ARCHITECTURE.md
§10 lists it that way: GitHub calls this path directly, it isn't part of
the versioned frontend-facing contract).

Everything here is transport concerns only: read the raw body before
touching JSON (signature verification needs the exact bytes GitHub signed,
not a re-serialization of the parsed payload), verify the signature,
dedup the delivery, and hand off to `application.webhooks
.handle_github_webhook` for the actual decision-making. The handler
returns fast in every case — indexing itself always happens in the worker,
never here.
"""

import logging

from fastapi import APIRouter, Header, Request, Response
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from lumora_api.application.webhooks.handle_github_webhook import process_push_event
from lumora_api.application.webhooks.schemas import GitHubPushPayload
from lumora_api.core.container import DbSessionDep, JobQueueDep, SettingsDep
from lumora_api.core.time import utcnow
from lumora_api.domain.webhook_security import verify_signature
from lumora_api.infrastructure.models import WebhookDelivery, WebhookDeliveryStatus

logger = logging.getLogger(__name__)

webhook_router = APIRouter(prefix="/webhooks", tags=["webhooks"])

_SUPPORTED_EVENTS = {"push"}


@webhook_router.post("/github", status_code=200)
async def github_webhook(
    request: Request,
    session: DbSessionDep,
    job_queue: JobQueueDep,
    settings: SettingsDep,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
    x_github_delivery: str | None = Header(default=None),
) -> Response:
    raw_body = await request.body()

    if not verify_signature(settings.github_webhook_secret, raw_body, x_hub_signature_256):
        return Response(status_code=401, content="invalid signature")

    if not x_github_delivery or not x_github_event:
        return Response(status_code=400, content="missing X-GitHub-Delivery/X-GitHub-Event header")

    delivery = WebhookDelivery(github_delivery_id=x_github_delivery, event_type=x_github_event)
    session.add(delivery)
    try:
        await session.commit()
    except IntegrityError:
        # UNIQUE(github_delivery_id) is the actual dedup guard, not this
        # try/except — this just turns the race into a 200 instead of a
        # 500 for whichever request loses it. See models.WebhookDelivery.
        await session.rollback()
        logger.info("Webhook delivery %s already processed — skipping", x_github_delivery)
        return Response(status_code=200)

    if x_github_event not in _SUPPORTED_EVENTS:
        await _mark_delivery(session, delivery, WebhookDeliveryStatus.IGNORED)
        return Response(status_code=200)

    try:
        payload = GitHubPushPayload.model_validate_json(raw_body)
    except ValidationError:
        await _mark_delivery(session, delivery, WebhookDeliveryStatus.FAILED)
        return Response(status_code=400, content="malformed push payload")

    try:
        await process_push_event(
            payload=payload, delivery_id=delivery.id, session=session, job_queue=job_queue
        )
    except Exception:
        logger.exception("Failed to process webhook delivery %s", x_github_delivery)
        await session.rollback()
        await _mark_delivery(session, delivery, WebhookDeliveryStatus.FAILED)
        # Still 200: GitHub retries on non-2xx, and retrying won't fix an
        # application bug — it would just redeliver into the same failure
        # (the delivery id is already recorded, so a redelivery would dedup
        # away anyway). The failure is visible in webhook_deliveries.status.
        return Response(status_code=200)

    await _mark_delivery(session, delivery, WebhookDeliveryStatus.QUEUED)
    return Response(status_code=200)


async def _mark_delivery(
    session: AsyncSession, delivery: WebhookDelivery, status: WebhookDeliveryStatus
) -> None:
    delivery.status = status
    delivery.processed_at = utcnow()
    await session.commit()
