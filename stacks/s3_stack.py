import aws_cdk as cdk
from aws_cdk import CfnOutput, Stack
from aws_cdk import (
    aws_s3 as s3,
)
from constructs import Construct

class S3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, config: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        bucket=s3.Bucket(self, prj_name+'-s3-bucket-'+config,
            access_control=s3.BucketAccessControl.BUCKET_OWNER_FULL_CONTROL,
            # encryption=s3.BucketEncryption.S3_MANAGED,
            # bucket_name=team+'-image',
            versioned=False,
            object_ownership=s3.ObjectOwnership.BUCKET_OWNER_ENFORCED,
            removal_policy=cdk.RemovalPolicy.RETAIN,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL
            # block_public_access=s3.BlockPublicAccess(
            #     block_public_acls=True,
            #     block_public_policy=True,
            #     ignore_public_acls=True,
            #     restrict_public_buckets=True
            # )
        )

        self.s3_output_1 = CfnOutput(self, 's3-output',
            value=bucket.bucket_name,
            export_name='s3-bucket-name-'+construct_id
        )
