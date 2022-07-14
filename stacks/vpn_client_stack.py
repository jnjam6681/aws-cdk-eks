from aws_cdk import CfnOutput, Stack
from aws_cdk import (
    aws_ec2 as ec2,
)
from constructs import Construct

class VPNClientStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, buildConfig: dict, sg: ec2.SecurityGroup, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        endpoint = ec2.ClientVpnEndpoint(self,
            "Endpoint",
            vpc=vpc,
            cidr='20.0.0.0/20',
            server_certificate_arn=buildConfig["server_certificate_arn"],
            client_certificate_arn=buildConfig["client_certificate_arn"],
            authorize_all_users_to_vpc_cidr=False,
            security_groups=[sg],
            self_service_portal=False,
            session_timeout=ec2.ClientVpnSessionTimeout.TWENTY_FOUR_HOURS,
            split_tunnel=True,
            vpc_subnets=ec2.SubnetSelection(
                one_per_az=False,
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
        )

        endpoint.add_authorization_rule("Rule",
            cidr=vpc.vpc_cidr_block,
            # group_id="group-id"
        )
