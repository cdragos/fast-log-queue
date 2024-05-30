import asyncio
import json
import logging
from itertools import islice
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from shared.models.log_entry import LogEntry
from shared.models.session import AsyncSessionLocal

logging.basicConfig(level=logging.DEBUG)

# Set the batch size for bulk insert into Postgres
# Even if the SQS is modified to send a large number of events, processing the records
# in smaller batches during the bulk insert helps avoid blocking the database for an
# extended period. This allows for better concurrency and prevents the database from
# becoming unresponsive.
BATCH_SIZE = 100

loop = asyncio.get_event_loop()


def batched(iterable, n):
    """Batch data into chunks of length n. The last batch may be shorter."""
    it = iter(iterable)
    while batch := list(islice(it, n)):
        yield batch


def extract_valid_records(records: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], set]:
    """Extract valid records and event IDs from the given list of records."""
    valid_records = []
    event_ids = set()
    for record in records:
        try:
            body = json.loads(record["body"])
            body["id"] = record["messageId"]
            valid_records.append(body)
            event_ids.add(record["messageId"])
        except (json.JSONDecodeError, KeyError) as e:
            logging.error(f"Invalid message format: {record['body']}. Error: {str(e)}")
    return valid_records, event_ids


async def process_log_entries(session: AsyncSession, records: list[dict[str, Any]], event_ids: set) -> list[LogEntry]:
    """
    Process log entries from the given records and event IDs.

    This function checks for existing event IDs in the database and creates
    LogEntry objects for new records.
    """
    existing_event_ids_result = await session.execute(select(LogEntry.event_id).where(LogEntry.event_id.in_(event_ids)))
    existing_event_ids = {row[0] for row in existing_event_ids_result}

    entities = []
    for record in records:
        if record["id"] in existing_event_ids:
            continue
        log_entry = LogEntry(event_id=record["id"], message=record["message"], level=record["level"])
        entities.append(log_entry)

    logging.debug(f"Processed {len(entities)} new log entries.")
    return entities


async def handle_event(event: dict) -> None:
    """Handle the incoming AWS SQS event."""
    logging.debug("Function triggered with payload")
    logging.debug(f"Event payload: {json.dumps(event)}")

    records = event.get("Records", [])
    async with AsyncSessionLocal() as session:
        for record_batch in batched(records, BATCH_SIZE):
            valid_records, event_ids = extract_valid_records(record_batch)

            try:
                entries = await process_log_entries(session, valid_records, event_ids)
                if entries:
                    session.add_all(entries)
                    await session.commit()
            except Exception as e:
                logging.error(f"Unexpected error: {e}")
                await session.rollback()

        await session.commit()

    logging.debug("Messages processed successfully")


def lambda_handler(event: dict, context: Any) -> None:
    """AWS Lambda handler function."""
    return loop.run_until_complete(handle_event(event))
