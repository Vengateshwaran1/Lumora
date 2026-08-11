"""DB-level dedup guarantee: `webhook_deliveries.github_delivery_id` is
UNIQUE, which is what actually makes concurrent-delivery dedup race-safe
(see infrastructure/models.WebhookDelivery and api/webhooks.py — the
application-level try/except around the insert is just what turns the
constraint violation into a 200 response, not the guard itself)."""

import uuid

import pytest
from sqlalchemy.exc import IntegrityError

from lumora_api.infrastructure.models import WebhookDelivery, WebhookDeliveryStatus


async def test_duplicate_github_delivery_id_is_rejected_by_the_database(db_session):
    delivery_id = str(uuid.uuid4())
    first = WebhookDelivery(github_delivery_id=delivery_id, event_type="push")
    db_session.add(first)
    await db_session.commit()

    second = WebhookDelivery(github_delivery_id=delivery_id, event_type="push")
    db_session.add(second)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()


async def test_distinct_delivery_ids_do_not_collide(db_session):
    a = WebhookDelivery(github_delivery_id=str(uuid.uuid4()), event_type="push")
    b = WebhookDelivery(github_delivery_id=str(uuid.uuid4()), event_type="push")
    db_session.add_all([a, b])
    await db_session.commit()  # must not raise

    assert a.status == WebhookDeliveryStatus.RECEIVED
    assert b.status == WebhookDeliveryStatus.RECEIVED
