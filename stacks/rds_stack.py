import json
import aws_cdk as cdk
from aws_cdk import CfnOutput, Stack
from aws_cdk import (
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_logs as logs,
    aws_secretsmanager as sm,
)
from constructs import Construct

class RDSStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, config: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        config_db = {}
        config_db['secret_string_template'] = json.dumps({'username': 'postgres'})
        config_db['version'] = rds.PostgresEngineVersion.VER_14_1
        config_db['subnet_type'] = ec2.SubnetType.PRIVATE_ISOLATED
        config_db['InstanceClass'] = ec2.InstanceClass.BURSTABLE3
        config_db['InstanceSize'] = ec2.InstanceSize.SMALL
        config_db['allocated_storage'] = 100
        config_db['max_allocated_storage'] = 150

        prj_name = self.node.try_get_context('project_name')

        rds_creds = sm.Secret(self, prj_name+'-db-secret-'+config,
            secret_name=prj_name+'/'+config+'/rds-secret',
            generate_secret_string=sm.SecretStringGenerator(
                include_space=False,
                password_length=12,
                generate_string_key='password',
                exclude_punctuation=True,
                secret_string_template=config_db['secret_string_template'],
            )
        )

        parameter_group = rds.ParameterGroup(self, prj_name+'-postgres-parameter-'+config,
            engine=rds.DatabaseInstanceEngine.postgres(version=config_db['version']),
            description='Parameter for Prynwan Postgresql'
        )

        db_postgres = rds.DatabaseInstance(self, construct_id,
            instance_identifier=construct_id,
            engine=rds.DatabaseInstanceEngine.postgres(version=config_db['version']),
            database_name="prynwan",
            # master_user=rds.Login(username='prynwan-user', password=rds_creds.secret_value_from_json('password')),
            instance_type=ec2.InstanceType.of(
                config_db['InstanceClass'], 
                config_db['InstanceSize']),
            credentials=rds.Credentials.from_secret(rds_creds),
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=config_db['subnet_type']
            ),
            vpc=vpc,
            multi_az=False,
            # storage_encrypted=True,
            storage_type=rds.StorageType.GP2,
            allocated_storage=config_db['allocated_storage'],
            max_allocated_storage=config_db['max_allocated_storage'],
            deletion_protection=True,
            backup_retention=cdk.Duration.days(7),
            monitoring_interval=cdk.Duration.seconds(60),
            cloudwatch_logs_retention=logs.RetentionDays.ONE_MONTH,
            enable_performance_insights=True,
            cloudwatch_logs_exports=['postgresql'],
            # auto_minor_version_upgrade=True,
            removal_policy=cdk.RemovalPolicy.SNAPSHOT,
            delete_automated_backups=True,
            parameter_group=parameter_group
        )

        db_postgres.connections.allow_default_port_from_any_ipv4()
        # db_postgres.connections.allow_default_port_from(postgres_sg, 'Allow traffic from ...')

        self.rds_output_1 = CfnOutput(self, 'rds-output-1',
            value=f'{rds_creds.secret_value}',
            description='secret value',
        )

        self.rds_output_2 = CfnOutput(self, 'rds-output-2',
            value=db_postgres.db_instance_endpoint_address,
            # description='secret value',
            export_name='rds-instance-endpoint-address-'+config
        )