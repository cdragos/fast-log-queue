import aws_cdk as cdk

from cdk.stack import FastLogQueueCdkStack

# Create a new CDK app
app = cdk.App()

# Retrieve the region from the CDK context or use the default value
region = app.node.try_get_context("region") or "us-east-1"
# Retrieve the account ID from the CDK context
account_id = app.node.try_get_context("account_id")

# Create a CDK environment using the account ID and region
env = cdk.Environment(account=account_id, region=region)

# Instantiate the FastLogQueueCdkStack with the app and environment
FastLogQueueCdkStack(app, "FastApiStack", env=env)

# Synthesize the CDK stack to generate the CloudFormation template
app.synth()
