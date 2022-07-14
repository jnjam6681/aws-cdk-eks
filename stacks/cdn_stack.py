from aws_cdk import CfnOutput, Stack
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cdn,
    aws_cloudfront_origins as origin,
    aws_certificatemanager as acm,
    aws_iam as iam,
)
from constructs import Construct 

class CDNStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, s3_bucket: str, buildConfig: dict, config: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context('project_name')

        bucket = s3.Bucket.from_bucket_name(self, 's3-bucket', s3_bucket)
        acm_arn=buildConfig["acm_arn"]
        certificate = acm.Certificate.from_certificate_arn(self, 'certificate', acm_arn)

        origin_access_identity = cdn.OriginAccessIdentity(self, prj_name+'-origin-access-dentity-'+config,
            comment=prj_name+'-origin-access-dentity-'+config
        )

        self.cdn_id = cdn.Distribution(self, prj_name+'-cdn-s3-image',
            default_behavior=cdn.BehaviorOptions(
                origin=origin.S3Origin(
                    bucket,
                    origin_access_identity=origin_access_identity
                ),
                # allowed_methods=cdn.AllowedMethods.ALLOW_ALL,
                viewer_protocol_policy=cdn.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            domain_names=['img.example.com'],
            certificate=certificate,
        )

        policy_statment_1 = iam.PolicyStatement()
        policy_statment_1.sid='allow-cdn'
        policy_statment_1.effect.ALLOW
        policy_statment_1.add_actions('s3:GetObject')
        policy_statment_1.add_resources(f'{bucket.bucket_arn}/*')
        policy_statment_1.add_canonical_user_principal(origin_access_identity.cloud_front_origin_access_identity_s3_canonical_user_id)

        policy_document = iam.PolicyDocument()
        policy_document.add_statements(policy_statment_1)

        s3.CfnBucketPolicy(self, prj_name+'-s3-policy-'+config,
            bucket=bucket.bucket_name,
            policy_document=policy_document
        )

        self.cdn_output_1 = CfnOutput(self, 'cdn-output',
            value=self.cdn_id.domain_name,
            export_name=prj_name+'-cdn-domain-name-'+config
        )