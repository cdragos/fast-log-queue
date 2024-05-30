import json
import uuid
from unittest.mock import patch

import pytest
from sqlalchemy import select

from shared.models.log_entry import LogEntry

pytestmark = pytest.mark.anyio


@pytest.fixture
def sqs_event():
    return {
        "Records": [
            {
                "messageId": str(uuid.uuid4()),
                "body": json.dumps({"message": "Test log entry 1", "level": "INFO"}),
            },
            {
                "messageId": str(uuid.uuid4()),
                "body": json.dumps({"message": "Test log entry 2", "level": "WARNING"}),
            },
        ]
    }


async def test_sqs_event_processor(async_db, sqs_event):
    from worker.main import handle_event

    with patch("worker.main.AsyncSessionLocal", return_value=async_db):
        await handle_event(sqs_event)

    entries = (await async_db.execute(select(LogEntry))).scalars().all()
    assert len(entries) == 2

    assert entries[0].message == "Test log entry 1"
    assert entries[0].level == "INFO"

    assert entries[1].message == "Test log entry 2"
    assert entries[1].level == "WARNING"
