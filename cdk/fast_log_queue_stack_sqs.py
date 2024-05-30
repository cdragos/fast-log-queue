from aws_cdk import Stack, aws_sqs as sqs
from constructs import Construct


class SqsStack(Stack):
    """
    AWS CDK Stack for creating an SQS queue.

    This stack creates an SQS queue for storing log messages.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.queue = self.create_sqs_queue()

    def create_sqs_queue(self) -> sqs.Queue:
        """Create an SQS queue for storing log messages."""
        return sqs.Queue(self, "FastLogQueue")
