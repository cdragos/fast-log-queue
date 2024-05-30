from aws_cdk import Stack, aws_ec2 as ec2, aws_rds as rds
from constructs import Construct

from .config import DATABASE_NAME


class DatabaseStack(Stack):
    """
    AWS CDK Stack for creating a PostgreSQL database.

    This stack creates a VPC and a PostgreSQL RDS instance within that VPC.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        self.vpc = ec2.Vpc(self, "VPC")
        self.database = self.create_postgres_database()

    def create_postgres_database(self):
        """Create a PostgreSQL RDS instance."""

        # Create a security group for the RDS instance
        security_group = ec2.SecurityGroup(self, "PostgresSG", vpc=self.vpc, allow_all_outbound=True)

        # Add an ingress rule to allow inbound PostgreSQL traffic from anywhere
        security_group.add_ingress_rule(
            ec2.Peer.ipv4("0.0.0.0/0"),
            ec2.Port.tcp(5432),
            "Allow inbound PostgreSQL traffic from anywhere",
        )

        return rds.DatabaseInstance(
            self,
            "PostgresDatabase",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_16_3),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            vpc=self.vpc,
            allocated_storage=20,
            database_name=DATABASE_NAME,
            credentials=rds.Credentials.from_generated_secret("postgres"),
            publicly_accessible=True,
            security_groups=[security_group],
        )
