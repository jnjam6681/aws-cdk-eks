from aws_cdk import Stack
from aws_cdk import (
    aws_ec2 as ec2,
)
from constructs import Construct

class SecurityStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        # self.postgres_sg = ec2.SecurityGroup(self, prj_name+'-postgres',
        #     security_group_name=prj_name+'-postgres-sg',
        #     vpc=vpc,
        #     description="SG for Service",
        #     allow_all_outbound=True
        # )

        self.vpn_client_prynwan_sg = ec2.SecurityGroup(self, prj_name+'-vpn-client',
            security_group_name=prj_name+'-vpn-client-prynwan-sg',
            vpc=vpc,
            # description="SG for Service",
            allow_all_outbound=True
        )
        # self.vpn_client_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(22), "SSH Access")
        self.vpn_client_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(5432), "Postgresql Access Private Network")