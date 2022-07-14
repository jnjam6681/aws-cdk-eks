#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.cdn_stack import CDNStack
from stacks.eks_stack import EKSStack
from stacks.s3_stack import S3Stack
from stacks.security_stack import SecurityStack
from stacks.vpc_stack import VPCStack
from stacks.rds_stack import RDSStack
from stacks.vpn_client_stack import VPNClientStack

app = cdk.App()

config = app.node.try_get_context('env')
print(config)
buildConfig = app.node.try_get_context(config)
print(buildConfig)

prj_name = app.node.try_get_context('project_name')

env = cdk.Environment(
    account=buildConfig['account'], 
    region=buildConfig['region']
)

vpc_stack = VPCStack(app, prj_name+'-vpc-stack-'+config, config=config, env=env)
security_stack = SecurityStack(app, prj_name+'-security-stack-'+config, vpc=vpc_stack.vpc, env=env)
rds_stack = RDSStack(app, prj_name+'-rds-platform-stack-'+config, vpc=vpc_stack.vpc, config=config, env=env)
s3_stack = S3Stack(app, prj_name+'-s3-platform-stack-'+config, config=config, env=env)
cdn_stack = CDNStack(app, prj_name+'-cdn-platform-stack-'+config, s3_bucket=cdk.Fn.import_value(s3_stack.s3_output_1.export_name), buildConfig=buildConfig['vpn-client'], config=config, env=env)
eks_stack = EKSStack(app, prj_name+'-eks-stack-'+config, buildConfig=buildConfig['eks'], vpc=vpc_stack.vpc, config=config, env=env)
vpn_cilent_stack = VPNClientStack(app, prj_name+'-vpn-client-stack-'+config, buildConfig=buildConfig['vpn-client'], sg=security_stack.vpn_client_sg, vpc=vpc_stack.vpc, env=env)

match config:
    case 'dev':
        cdk.Tags.of(app).add('environment', 'develop')
    case 'uat':
        cdk.Tags.of(app).add('environment', 'uat')
    case 'prod':
        cdk.Tags.of(app).add('environment', 'production')
    
cdk.Tags.of(app).add('project', prj_name)

app.synth()
