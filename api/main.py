import json
from http import HTTPStatus

from botocore.exceptions import ClientError
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from mangum import Mangum
from pydantic import BaseModel

from api.sqs_client import sqs
from shared.config import settings


class LogEntrySchema(BaseModel):
    message: str
    level: str


class SQSClientError(HTTPException):
    def __init__(self, message: str):
        super().__init__(status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=message)


app = FastAPI()


@app.exception_handler(SQSClientError)
async def sqs_client_error_handler(request: Request, exc: SQSClientError):
    return JSONResponse(
        status_code=exc.status_code, content={"message": f"Error occurred while sending message to SQS: {exc.detail}"}
    )


@app.post("/logs")
async def logs(log_entry_schema: LogEntrySchema):
    message = json.dumps(log_entry_schema.dict())
    try:
        sqs.send_message(QueueUrl=settings.QUEUE_URL, MessageBody=message)
    except ClientError as exc:
        raise SQSClientError(str(exc))

    return {"message": "Log entry queued for processing"}


handler = Mangum(app)
