from aws_cdk import (
    BundlingOptions,
    CfnOutput,
    Duration,
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_rds as rds,
    aws_sqs as sqs,
)
from aws_cdk.aws_apigatewayv2 import CorsHttpMethod, CorsPreflightOptions, HttpApi, HttpMethod
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct


class FastLogQueueCdkStack(Stack):
    """
    AWS CDK Stack to deploy a FastAPI application with PostgreSQL and SQS integration.

    This stack sets up:
    - An SQS queue for logging messages.
    - A VPC for networking resources.
    - A PostgreSQL RDS instance.
    - A Lambda function to handle API requests.
    - An HTTP API Gateway to route requests to the Lambda function.
    """

    DATABASE_NAME = "fastlogqueue"

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.create_sqs_queue()
        self.create_vpc()
        self.create_postgres_database()
        self.create_api_lambda_function()
        self.create_http_api()

    def create_vpc(self) -> None:
        """Create a VPC for the RDS instance"""
        self.vpc = ec2.Vpc(self, "VPC")

    def create_sqs_queue(self) -> None:
        """Create an SQS queue for storing log messages"""
        self.queue = sqs.Queue(self, "FastLogQueue")

    def create_postgres_database(self) -> None:
        """Create an RDS instance for the PostgreSQL database."""
        self.postgres_database = rds.DatabaseInstance(
            self,
            "PostgresDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16_3),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            vpc=self.vpc,
            allocated_storage=20,
            database_name=self.DATABASE_NAME,
            credentials=rds.Credentials.from_generated_secret("postgres"),
        )

    def create_api_lambda_role(self) -> iam.Role:
        """Create an IAM role for the API Lambda function with necessary permissions."""
        # Create an IAM role for the API Lambda function
        # Grant the necessary permissions to the role
        return iam.Role(
            self,
            "ApiLambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSQSFullAccess"),
            ],
        )

    def create_api_lambda_function(self) -> None:
        """
        Create a Lambda function to handle API requests.
        The function is granted necessary permissions through an IAM role.
        """
        # Create an IAM role for the API Lambda function
        api_lambda_role = self.create_api_lambda_role()
        self.api_handler = _lambda.Function(
            self,
            "ApiHandler",
            code=self.create_api_lambda_code(),
            runtime=_lambda.Runtime.PYTHON_3_11,
            architecture=_lambda.Architecture.ARM_64,
            handler="api.main.handler",
            role=api_lambda_role,
            memory_size=128,
            timeout=Duration.seconds(29),
            environment={
                "POSTGRES_USER": self.postgres_database.secret.secret_value_from_json("username").unsafe_unwrap(),
                "POSTGRES_SERVER": self.postgres_database.db_instance_endpoint_address,
                "POSTGRES_PORT": str(self.postgres_database.db_instance_endpoint_port),
                "POSTGRES_PASSWORD": self.postgres_database.secret.secret_value_from_json("password").unsafe_unwrap(),
                "POSTGRES_DB": self.DATABASE_NAME,
            },
        )

    def create_api_lambda_code(self) -> _lambda.Code:
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

    def create_http_api(self) -> None:
        """Create an HTTP API Gateway with CORS configuration and integrate it with the API Lambda function."""
        # Create an HTTP API Gateway
        http_api = HttpApi(
            self,
            "HttpApiGateway",
            cors_preflight=CorsPreflightOptions(
                allow_headers=["Authorization", "Content-Type"],
                allow_methods=[
                    CorsHttpMethod.OPTIONS,
                    CorsHttpMethod.GET,
                    CorsHttpMethod.HEAD,
                    CorsHttpMethod.POST,
                ],
                allow_origins=["*"],
                max_age=Duration.days(10),
            ),
        )

        # Add routes to the HTTP API Gateway
        # Integrate the routes with the API Lambda function
        http_api.add_routes(
            path="/{proxy+}",
            methods=[HttpMethod.ANY],
            integration=HttpLambdaIntegration("ApiIntegration", handler=self.api_handler),
        )

        # Output the URL of the HTTP API Gateway
        CfnOutput(self, "HttpApiGatewayUrl", value=http_api.url or "")
