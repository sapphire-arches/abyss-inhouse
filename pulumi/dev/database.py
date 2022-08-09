#
# Deploys the required postgresql database
#
import base64

import pulumi
from pulumi import ComponentResource
from pulumi import Output
from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import Secret
from pulumi_kubernetes.meta.v1 import ObjectMetaArgs
from pulumi_kubernetes.helm.v3 import Chart
from pulumi_kubernetes.helm.v3 import ChartOpts
from pulumi_kubernetes.helm.v3 import FetchOpts
from pulumi_kubernetes.rbac.v1 import PolicyRuleArgs
from pulumi_kubernetes.rbac.v1 import Role
from pulumi_kubernetes.rbac.v1 import RoleRefArgs
from pulumi_kubernetes.rbac.v1 import RoleBinding
from pulumi_kubernetes.rbac.v1 import SubjectArgs
from pulumi_kubernetes_cert_manager import CertManager
from pulumi_random import RandomPassword


def encode_secret(s):
    return base64.b64encode(s.encode('utf-8')).decode('utf-8')


class Database(ComponentResource):
    postgres_password: Output[str]
    replication_password: Output[str]

    def __init__(self,
                 name: str,
                 deploy_volumes: bool,
                 certmanager: CertManager,
                 opts: ResourceOptions = None):
        super().__init__('abyss:component:Database', name, {}, opts)
        size = "10Gi"

        self.postgres_password = RandomPassword(
            name + '-postgress-password',
            length=16,
            special=False,
            opts=ResourceOptions(parent=self)).result

        self.replication_password = RandomPassword(
            name + '-replication-password',
            length=16,
            special=False,
            opts=ResourceOptions(parent=self)).result

        self.patroni_admin_password = RandomPassword(
            name + '-admin-password',
            length=16,
            special=False,
            opts=ResourceOptions(parent=self)).result

        secret = Secret(
            name,
            string_data={
                'PATRONI_SUPERUSER_PASSWORD': self.postgres_password,
                'PATRONI_REPLICATION_PASSWORD': self.replication_password,
                'PATRONI_admin_PASSWORD': self.patroni_admin_password,
            },
            opts=ResourceOptions(parent=self),
        )

        chart_deps = [certmanager, secret]
        if deploy_volumes:
            from dev.storage import make_volume
            for i in range(3):
                chart_deps.append(
                    make_volume(f'{name}-abyss-timescaledb-data-{i}', '6Gi',
                                'abyss-timescaledb-data',
                                ResourceOptions(parent=self)))
                chart_deps.append(
                    make_volume(f'{name}-abyss-timescaledb-wal-{i}', '3Gi',
                                'abyss-timescaledb-wal',
                                ResourceOptions(parent=self)))

        role = Role(
                name,
                metadata=ObjectMetaArgs(
                    # Turn off autonaming so the chart works
                    name=name + '-timescaledb'
                ),
                rules=[
                    PolicyRuleArgs(
                        api_groups=[""],
                        verbs=[ "create", "get", "list", "patch", "update", "watch", "delete", ],
                        resources=[ "configmaps" ],
                    ),
                    PolicyRuleArgs(
                        api_groups=[""],
                        verbs=[ "create", "get", "list", "patch", "update", "watch", "delete", ],
                        resources=[ "endpoints", "endpoints/restricted" ],
                    ),
                    PolicyRuleArgs(
                        api_groups=[""],
                        verbs=[ "get", "list", "patch", "update", "watch", ],
                        resources=[ "pods" ],
                    ),
                    PolicyRuleArgs(
                        api_groups=[""],
                        verbs=[ "create", "get", "list", "patch", "update", "watch", "delete", ],
                        resources=[ "services" ],
                    ),
                ],
                opts=ResourceOptions(parent=self),
            )
        chart_deps.append(role)

        rolebinding = RoleBinding(
                name,
                metadata=ObjectMetaArgs(
                    # Turn off autonaming so the chart works
                    name=name + '-timescaledb'
                ),
                role_ref=RoleRefArgs(
                    api_group='rbac.authorization.k8s.io',
                    kind='Role',
                    name=name + '-timescaledb',
                ),
                subjects=[
                    SubjectArgs(kind='ServiceAccount', name=name+'-timescaledb'),
                ],
                opts=ResourceOptions(parent=self),
                )
        chart_deps.append(rolebinding)

        chart = Chart('db',
                      ChartOpts(chart='timescaledb-single',
                                version='0.14.0',
                                fetch_opts=FetchOpts(
                                    repo='https://charts.timescale.com/'),
                                values={
                                    'secrets': {
                                        'credentialsSecretName': secret.id.apply(lambda s: s[s.find('/')+1:]),
                                    },
                                    'backup': {
                                        'enabled': False,
                                    },
                                    'loadBalancer': {
                                        'enabled': False,
                                    },
                                    'persistentVolumes': {
                                        'data': {
                                            'storageClass':
                                            'abyss-timescaledb-data',
                                        },
                                        'wal': {
                                            'storageClass':
                                            'abyss-timescaledb-wal',
                                        }
                                    },
                                    'rbac': {
                                        # Disable RBAC creates because we do it
                                        # manually above, 'cause the ones that
                                        # ship are broken
                                        'create': False,
                                    },
                                    'replicaCount': 3,
                                }),
                      opts=ResourceOptions(parent=self, depends_on=chart_deps))
