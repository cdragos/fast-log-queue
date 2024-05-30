from aws_cdk import (
    BundlingOptions,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_lambda_event_sources as lambda_event_sources,
)
from constructs import Construct

from .config import BATCH_SIZE, DATABASE_NAME


class LambdaStack(Stack):
    """
    AWS CDK Stack for creating Lambda functions.

    This stack creates the following Lambda functions:
    - API Handler: Handles incoming API requests and interacts with the database and SQS queue.
    - Worker: Processes messages from the SQS queue and writes log entries to the database.
    - Migration Handler: Runs database migrations.

    The stack also creates the necessary IAM roles and permissions for the Lambda functions.
    """

    def __init__(self, scope: Construct, construct_id: str, vpc, database, queue, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = vpc
        self.database = database
        self.queue = queue

        # Create IAM roles for the Lambda functions
        self.lambda_db_role = self.create_lambda_db_role()
        self.lambda_role = self.create_lambda_role()

        # Create the Lambda functions
        self.api_handler = self.create_api_lambda_function()
        self.worker_handler = self.create_worker_lambda_function()
        self.migration_handler = self.create_migration_lambda_function()

    def create_lambda_db_role(self):
        """Create an IAM role for Lambda functions with necessary database access and VPC permissions"""

        role = iam.Role(
            self,
            "LambdaDatabaseAccessRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRDSFullAccess"),
            ],
        )

        # Add permissions to create, describe, and delete network interfaces
        role.add_to_policy(
            iam.PolicyStatement(
                actions=["ec2:CreateNetworkInterface", "ec2:DescribeNetworkInterfaces", "ec2:DeleteNetworkInterface"],
                resources=["*"],
            )
        )

        return role

    def create_lambda_role(self):
        """Create an IAM role for Lambda functions with necessary permissions."""

        role = iam.Role(
            self,
            "LambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRDSFullAccess"),
            ],
        )

        # Add permissions to create, describe, and delete network interfaces
        role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:CreateNetworkInterface",
                    "ec2:DescribeNetworkInterfaces",
                    "ec2:DeleteNetworkInterface",
                ],
                resources=["*"],
            )
        )

        return role

    def create_api_lambda_function(self):
        """
        Create a Lambda function to handle API requests.
        The function is granted necessary permissions through an IAM role.
        """

        return _lambda.Function(
            self,
            "ApiHandler",
            code=self.create_api_lambda_code(),
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="api.main.handler",
            role=self.lambda_role,
            memory_size=128,
            timeout=Duration.seconds(29),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.database.connections.security_groups[0]],
            environment={
                "POSTGRES_USER": self.database.secret.secret_value_from_json("username").unsafe_unwrap(),
                "POSTGRES_SERVER": self.database.db_instance_endpoint_address,
                "POSTGRES_PORT": str(self.database.db_instance_endpoint_port),
                "POSTGRES_PASSWORD": self.database.secret.secret_value_from_json("password").unsafe_unwrap(),
                "POSTGRES_DB": DATABASE_NAME,
                "QUEUE_URL": self.queue.queue_url,
            },
        )

    def create_api_lambda_code(self):
        """Create the API Lambda function code by bundling the necessary files and dependencies."""

        # Bundle the Lambda function code and dependencies
        # Install the required packages and copy the necessary files
        return _lambda.Code.from_asset(
            ".",
            bundling=BundlingOptions(
                image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                command=[
                    "bash",
                    "-c",
                    (
                        "pip install -r requirements.txt -t /asset-output && "
                        "cp -au api /asset-output && "
                        "cp -au shared /asset-output"
                    ),
                ],
            ),
        )

    def create_worker_lambda_function(self):
        """
        Create a Lambda function to process messages from the SQS queue.
        The function is granted necessary permissions through an IAM role.
        """
        worker_handler = _lambda.Function(
            self,
            "WorkerHandler",
            code=self.create_worker_lambda_code(),
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="worker.main.lambda_handler",
            role=self.lambda_role,
            memory_size=128,
            timeout=Duration.seconds(29),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.database.connections.security_groups[0]],
            environment={
                "POSTGRES_USER": self.database.secret.secret_value_from_json("username").unsafe_unwrap(),
                "POSTGRES_SERVER": self.database.db_instance_endpoint_address,
                "POSTGRES_PORT": str(self.database.db_instance_endpoint_port),
                "POSTGRES_PASSWORD": self.database.secret.secret_value_from_json("password").unsafe_unwrap(),
                "POSTGRES_DB": DATABASE_NAME,
            },
        )

        # Add an SQS event source to trigger the worker Lambda function
        worker_handler.add_event_source(lambda_event_sources.SqsEventSource(self.queue, batch_size=BATCH_SIZE))
        return worker_handler

    def create_worker_lambda_code(self):
        """Create the worker Lambda function code by bundling the necessary files and dependencies."""

        # Bundle the Lambda function code and dependencies
        # Install the required packages and copy the necessary files
        return _lambda.Code.from_asset(
            ".",
            bundling=BundlingOptions(
                image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                command=[
                    "bash",
                    "-c",
                    (
                        "pip install -r requirements.txt -t /asset-output && "
                        "cp -au worker /asset-output && "
                        "cp -au shared /asset-output"
                    ),
                ],
            ),
        )

    def create_migration_lambda_function(self):
        """Create a Lambda function to run database migrations."""

        return _lambda.Function(
            self,
            "MigrationHandler",
            code=_lambda.Code.from_asset(
                ".",
                bundling=BundlingOptions(
                    image=_lambda.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        (
                            "pip install -r requirements.txt -t /asset-output && "
                            "cp -au alembic_migrations /asset-output && "
                            "cp -au alembic.ini /asset-output && "
                            "cp -au shared /asset-output && "
                            "cp -au cdk/lambda/migration.py /asset-output"
                        ),
                    ],
                ),
            ),
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="migration.handler",
            role=self.lambda_db_role,
            memory_size=128,
            timeout=Duration.seconds(60),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[self.database.connections.security_groups[0]],
            environment={
                "POSTGRES_USER": self.database.secret.secret_value_from_json("username").unsafe_unwrap(),
                "POSTGRES_SERVER": self.database.db_instance_endpoint_address,
                "POSTGRES_PORT": str(self.database.db_instance_endpoint_port),
                "POSTGRES_PASSWORD": self.database.secret.secret_value_from_json("password").unsafe_unwrap(),
                "POSTGRES_DB": DATABASE_NAME,
            },
        )
