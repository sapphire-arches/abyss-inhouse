#
# Deploy jaeger for tracing/log collection
#

import pulumi
from pulumi import ComponentResource
from pulumi import Output
from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import Namespace
from pulumi_kubernetes.helm.v3 import Chart
from pulumi_kubernetes.helm.v3 import ChartOpts
from pulumi_kubernetes.helm.v3 import FetchOpts
from pulumi_kubernetes.yaml import ConfigFile
from pulumi_kubernetes_cert_manager import CertManager


class JaegerDeployment(ComponentResource):

    def __init__(self,
                 certmanager: CertManager,
                 ingress,
                 deploy_elastic: bool,
                 opts: ResourceOptions = None):
        super().__init__('abyss:component:Jaeger', 'jaeger', {}, opts)

        """
        chart_deps = [certmanager, ingress]
        if deploy_elastic:
            from dev.storage import make_volume
            for volume in range(0, 3):
                volume = make_volume(f'abyss-jaegger-es-{volume}', '6Gi', 'abyss-jaeger-es', ResourceOptions(parent=self))
                chart_deps.append(volume)

        chart = Chart(
            'jaeger',
            ChartOpts(
                # namespace=namespace.id,
                chart='jaeger',
                version='0.57.1',
                fetch_opts=FetchOpts(
                    repo='https://jaegertracing.github.io/helm-charts'),
                # TODO: have a non-dev config
                values={
                    'provisionDataStore': {
                        'cassandra': False,
                        'elasticsearch': deploy_elastic,
                        'kafka': False,
                    },
                    'storage': {
                        'type': 'elasticsearch',
                    },
                    'elasticsearch': {
                        'sysctlInitContainer': {
                            'enabled': False,
                        },
                        'volumeClaimTemplate': {
                            'resources': {
                                'requests': {
                                    'storage': '5Gi'
                                }
                            },
                            'storageClassName': 'abyss-jaeger-es',
                        },
                        # Disable hard anti-affinity because we want to run on just 1 node for dev
                        'antiAffinity': 'soft',
                    },
                    'allInOne': {
                        'enabled': False,
                    },
                    'agent': {
                        'enabled': False,
                    },
                    'collector': {
                        'enabled': True,
                        'ingress': {
                            'enabled': False,
                        },
                        'service': {
                            'otlp': {
                                'grpc': {
                                    'port': 4317
                                }
                            }
                        }
                    },
                    'query': {
                        'enabled': True,
                        'ingress': {
                            'enabled': True,
                            'hosts': [
                                'jaeger.cluster.local',
                            ],
                            'annotations': {
                                'kubernetes.io/ingress.class': 'nginx'
                            },
                        },
                    },
                },
                transformations=[
                    # set_sc,
                ]),
            opts=ResourceOptions(parent=self, depends_on=chart_deps),
        )

        query_svc = chart.get_resource('v1/Service', 'jaeger-query')

        pulumi.export('jaeger-host', query_svc.spec.cluster_ip)
        """
