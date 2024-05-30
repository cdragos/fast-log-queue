import logging
from http import HTTPStatus
from typing import Literal

from botocore.exceptions import ClientError
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.middleware.cors import CORSMiddleware

from api.sqs_client import sqs
from shared.config import settings
from shared.models.database_dependency import get_async_db
from shared.models.log_entry import LogEntry

logging.basicConfig(level=logging.DEBUG)


class LogEntrySchema(BaseModel):
    """Schema for log entry payload."""

    message: str
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


class SQSClientError(HTTPException):
    """Custom exception for SQS client errors."""

    def __init__(self, message: str):
        super().__init__(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=message)


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "HEAD", "PUT", "DELETE", "PATCH", "OPTIONS", "*"],
    allow_headers=["Authorization", "*"],
)


@app.exception_handler(SQSClientError)
async def handle_sqs_client_error(request: Request, exc: SQSClientError) -> JSONResponse:
    """Exception handler for SQSClientError."""
    logging.error(f"SQSClientError: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code, content={"message": f"Error occurred while sending message to SQS: {exc.detail}"}
    )


@app.post("/logs")
async def logs(log_entry_schema: LogEntrySchema) -> dict[str, str]:
    """ "Endpoint to handle log entries."""
    message = log_entry_schema.json()
    logging.debug(f"Received log entry: {message}")
    try:
        sqs.send_message(QueueUrl=settings.QUEUE_URL, MessageBody=message)
    except ClientError as exc:
        raise SQSClientError(str(exc))

    return {"message": "Log entry queued for processing"}


@app.get("/logs")
async def get_logs(db: AsyncSession = Depends(get_async_db)):
    """Retrieve the latest log entries from the database."""
    query = select(LogEntry).order_by(LogEntry.timestamp.desc()).limit(5)
    result = await db.execute(query)
    logs = result.scalars().all()

    return [
        {
            "id": log.id,
            "event_id": log.event_id,
            "message": log.message,
            "level": log.level,
            "timestamp": log.timestamp.isoformat(),
        }
        for log in logs
    ]


handler = Mangum(app)
