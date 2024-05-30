from aws_cdk import Stack
from constructs import Construct

from .fast_log_queue_stack_api_gateway import ApiGatewayStack
from .fast_log_queue_stack_database import DatabaseStack
from .fast_log_queue_stack_lambda import LambdaStack
from .fast_log_queue_stack_sqs import SqsStack


class FastLogQueueCdkStack(Stack):
    """
    AWS CDK Stack to deploy a FastAPI application with PostgreSQL and SQS integration.

    This stack sets up the following resources:
    - An SQS queue for logging messages.
    - A VPC for networking resources.
    - A PostgreSQL RDS instance for storing log entries.
    - An API Lambda function to handle incoming API requests.
    - A worker Lambda function to process messages from the SQS queue.
    - A migration Lambda function to run database migrations.
    - An HTTP API Gateway to route requests to the API Lambda function.
    - Necessary IAM roles and permissions for the Lambda functions.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        database_stack = DatabaseStack(self, "DatabaseStack")
        sqs_stack = SqsStack(self, "SqsStack")
        lambda_stack = LambdaStack(
            self, "LambdaStack", vpc=database_stack.vpc, database=database_stack.database, queue=sqs_stack.queue
        )
        ApiGatewayStack(self, "ApiGatewayStack", api_handler=lambda_stack.api_handler)
