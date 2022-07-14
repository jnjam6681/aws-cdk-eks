# import aws_cdk as cdk
from aws_cdk import CfnOutput, Stack
from aws_cdk import (
    aws_iam as iam,
    aws_eks as eks,
    aws_ec2 as ec2,
)
from constructs import Construct

class EKSStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, buildConfig: dict, vpc: ec2.Vpc, config: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        prj_name = self.node.try_get_context("project_name")

        if (buildConfig["create_new_cluster_admin_role"] == "True"):
            cluster_admin_role = iam.Role(self, "ClusterAdminRole",
                assumed_by=iam.CompositePrincipal(
                    iam.AccountRootPrincipal(),
                    iam.ServicePrincipal(
                        "ec2.amazonaws.com")
                )
            )
            cluster_admin_policy_statement_json_1 = {
                "Effect": "Allow",
                "Action": [
                    "eks:DescribeCluster"
                ],
                "Resource": "*"
            }
            cluster_admin_role.add_to_principal_policy(
                iam.PolicyStatement.from_json(cluster_admin_policy_statement_json_1))
        else:
            cluster_admin_role = iam.Role.from_role_arn(self, "ClusterAdminRole", role_arn=buildConfig["existing_admin_role_arn"])

        eks_cluster = eks.Cluster(
            self, "Cluster",
            cluster_name=prj_name+"-eks-cluster-"+config,
            vpc=vpc,
            masters_role=cluster_admin_role,
            # Make our cluster's control plane accessible only within our private VPC
            # This means that we'll have to ssh to a jumpbox/bastion or set up a VPN to manage it
            endpoint_access=eks.EndpointAccess.PUBLIC,
            version=eks.KubernetesVersion.of(buildConfig["eks_version"]),
            default_capacity=0,
            cluster_logging=[eks.ClusterLoggingTypes.API, 
                            eks.ClusterLoggingTypes.AUDIT,
                            eks.ClusterLoggingTypes.AUTHENTICATOR, 
                            eks.ClusterLoggingTypes.CONTROLLER_MANAGER,
                            eks.ClusterLoggingTypes.SCHEDULER]
        )
        
        if (buildConfig["eks_deploy_managed_nodegroup"] == "True"):
            # Parse the instance types as comma seperated list turn into instance_types[]
            instance_types_context = buildConfig["eks_node_instance_type"].split(",")

            instance_types = []
            for value in instance_types_context:
                instance_type = ec2.InstanceType(value)
                instance_types.append(instance_type)

            eks_node_group = eks_cluster.add_nodegroup_capacity(
                "cluster-default-ng",
                capacity_type=eks.CapacityType.ON_DEMAND,
                desired_size=2,
                min_size=1,
                max_size=5,
                disk_size=20,
                # The default in CDK is to force upgrades through even if they violate - it is safer to not do that
                force_update=False,
                instance_types=instance_types,
                # https://docs.amazonaws.cn/en_us/eks/latest/userguide/eks-linux-ami-versions.html
                release_version=buildConfig["eks_node_ami_version"]
            )
            eks_node_group.role.add_managed_policy(
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))

        if (buildConfig["deploy_cluster_autoscaler"] == "True"):
            clusterautoscaler_service_account = eks_cluster.add_service_account(
                "clusterautoscaler",
                name="clusterautoscaler",
                namespace="kube-system"
            )

            # Create the PolicyStatements to attach to the role
            clusterautoscaler_policy_statement_json_1 = {
                "Effect": "Allow",
                "Action": [
                    "autoscaling:DescribeAutoScalingGroups",
                    "autoscaling:DescribeAutoScalingInstances",
                    "autoscaling:DescribeLaunchConfigurations",
                    "autoscaling:DescribeTags",
                    "autoscaling:SetDesiredCapacity",
                    "autoscaling:TerminateInstanceInAutoScalingGroup",
                    "ec2:DescribeLaunchTemplateVersions"
                ],
                "Resource": "*"
            }

            # Attach the necessary permissions
            clusterautoscaler_service_account.add_to_principal_policy(
                iam.PolicyStatement.from_json(clusterautoscaler_policy_statement_json_1))

            # Install the Cluster Autoscaler
            # For more info see https://github.com/kubernetes/autoscaler/tree/master/charts/cluster-autoscaler
            clusterautoscaler_chart = eks_cluster.add_helm_chart(
                "cluster-autoscaler",
                chart="cluster-autoscaler",
                version="9.19.2",
                release="clusterautoscaler",
                repository="https://kubernetes.github.io/autoscaler",
                namespace="kube-system",
                values={
                    "autoDiscovery": {
                        "clusterName": eks_cluster.cluster_name
                    },
                    "awsRegion": self.region,
                    "rbac": {
                        "serviceAccount": {
                            "create": False,
                            "name": "clusterautoscaler"
                        }
                    },
                    "replicaCount": 2,
                    "extraArgs": {
                        "skip-nodes-with-system-pods": False,
                        "balance-similar-node-groups": True
                    }
                }
            )
            clusterautoscaler_chart.node.add_dependency(
                clusterautoscaler_service_account)

        if (buildConfig["deploy_metrics_server"] == "True"):
            # For more info see https://github.com/kubernetes-sigs/metrics-server/tree/master/charts/metrics-server
            # Changed from the Bitnami chart for Graviton/ARM64 support
            metricsserver_chart = eks_cluster.add_helm_chart(
                "metrics-server",
                chart="metrics-server",
                version="3.8.2",
                release="metricsserver",
                repository="https://kubernetes-sigs.github.io/metrics-server/",
                namespace="kube-system",
                values={
                    "resources": {
                        "requests": {
                            "cpu": "0.25",
                            "memory": "0.5Gi"
                        }
                    }
                }
            )

        CfnOutput(
            self, "eks-cluster-name-output",
            value=eks_cluster.cluster_name,
            export_name="eks-cluster-name"
        )

        CfnOutput(
            self, "eks-cluster-iodc-provider-arn-output",
            value=eks_cluster.open_id_connect_provider.open_id_connect_provider_arn,
            export_name="eks-cluster-iodc-provider-arn"
        )

        CfnOutput(
            self, "eks-cluster-kubectl-role-arn-output",
            value=eks_cluster.kubectl_role.role_arn,
            export_name="eks-cluster-kubectl-role-arn"
        )

        CfnOutput(
            self, "eks-sg-id-output",
            value=eks_cluster.kubectl_security_group.security_group_id,
            export_name="eks-sg-id"
        )