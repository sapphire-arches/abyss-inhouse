#
# Deploy jaeger for tracing/log collection
#

import pulumi
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_kubernetes.core.v1 import (
    Namespace,
)
from pulumi_kubernetes.yaml import ConfigFile
from pulumi_kubernetes_cert_manager import CertManager
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)
from ingress import Ingress

class JaegerDeployment(ComponentResource):
    def __init__(self, certmanager: CertManager, opts: ResourceOptions = None):
        super().__init__('abyss:component:Jaeger', 'jaeger', {}, opts)

        # Jaeger operator defaults to the "observability" namespace, so make
        # sure it exists.

        namespace = Namespace("observability", opts=ResourceOptions(parent=self))

        pulumi.export('obs-ns', namespace.id)

        chart = Chart(
            'jaeger',
            ChartOpts(
                # namespace=namespace.id,
                chart='jaeger',
                version='0.57.1',
                fetch_opts=FetchOpts(
                    repo='https://jaegertracing.github.io/helm-charts'
                ),
                # TODO: have a non-dev config
                values={
                    'provisionDataStore': {
                        'cassandra': False,
                        'elasticsearch': False,
                        'kafka': False,
                    },
                    'storage': {
                        'type': 'memory',
                    },
                    'allInOne': {
                        'enabled': False,
                    },
                    'agent':{
                        'enabled': True,
                    },
                    'collector': {
                        'enabled': True,
                        'ingress': {
                            'enabled': False,
                        },
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
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    namespace,
                ]
            ),
        )

        query_svc = chart.get_resource('v1/Service', 'jaeger-query')

        pulumi.export('jaeger-host', query_svc.spec.cluster_ip)
