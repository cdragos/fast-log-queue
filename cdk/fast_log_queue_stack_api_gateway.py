from aws_cdk import CfnOutput, Duration, Stack
from aws_cdk.aws_apigatewayv2 import CorsHttpMethod, CorsPreflightOptions, HttpApi, HttpMethod
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from constructs import Construct


class ApiGatewayStack(Stack):
    """
    AWS CDK Stack for creating an HTTP API Gateway.

    This stack sets up an HTTP API Gateway with CORS configuration and integrates it with a provided Lambda function.
    """

    def __init__(self, scope: Construct, construct_id: str, api_handler, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.api_handler = api_handler
        self.create_http_api()

    def create_http_api(self):
        """Create an HTTP API Gateway with CORS configuration and integrate it with the API Lambda function."""

        # Create an HTTP API Gateway with CORS configuration
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

        # Add routes to the HTTP API Gateway and integrate with the API Lambda function
        http_api.add_routes(
            path="/{proxy+}",
            methods=[HttpMethod.ANY],
            integration=HttpLambdaIntegration("ApiIntegration", handler=self.api_handler),
        )

        # Output the URL of the HTTP API Gateway
        CfnOutput(self, "HttpApiGatewayUrl", value=http_api.url or "")
