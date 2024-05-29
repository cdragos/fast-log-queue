import json
from http import HTTPStatus
from unittest.mock import patch

import boto3
import pytest
from botocore.exceptions import ClientError
from moto import mock_aws

from shared.config import settings

pytestmark = pytest.mark.anyio


QUEUE_NAME = "test-queue"


@pytest.fixture
def sqs_client(monkeypatch):
    with mock_aws():
        sqs = boto3.client("sqs", region_name="us-east-1")
        queue = sqs.create_queue(QueueName=QUEUE_NAME)
        monkeypatch.setattr(settings, "QUEUE_URL", queue["QueueUrl"])
        yield sqs


async def test_logs_endpoint_successfully_queues_log_entry(async_client, sqs_client):
    payload = {"message": "Test log entry", "level": "INFO"}

    url = async_client._transport.app.url_path_for("logs")
    resp = await async_client.post(url, json=payload)

    assert resp.status_code == HTTPStatus.OK
    assert resp.json() == {"message": "Log entry queued for processing"}

    messages = sqs_client.receive_message(QueueUrl=settings.QUEUE_URL)
    assert "Messages" in messages

    message = messages["Messages"][0]
    assert json.loads(message["Body"]) == payload


async def test_logs_endpoint_handles_sqs_client_error(async_client, monkeypatch):
    with patch("api.main.sqs") as mock_sqs_client:
        mock_sqs_client.send_message.side_effect = ClientError({"Error": {"Message": "Test error"}}, "SendMessage")
        payload = {"message": "Test log entry", "level": "INFO"}
        url = async_client._transport.app.url_path_for("logs")
        resp = await async_client.post(url, json=payload)
        assert resp.status_code == HTTPStatus.INTERNAL_SERVER_ERROR
        assert resp.json() == {
            "message": "Error occurred while sending message to SQS: An error occurred (Unknown) when calling the SendMessage operation: Test error"
        }
