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

def remove_status(obj, opts):
    """ Stupid hack transformer to deal with jaeger operator trying to set
    status """
    if obj["kind"] == "CustomResourceDefinition":
        del obj["status"]

# Make every service private to the cluster, i.e., turn all services into ClusterIP instead of LoadBalancer.
def make_service_private(obj, opts):
    if obj["kind"] == "Service" and obj["apiVersion"] == "v1":
        try:
            t = obj["spec"]["type"]
            if t == "LoadBalancer":
                pulumi.info(f'Replacing LB with CIP')
                obj["spec"]["type"] = "ClusterIP"
        except KeyError:
            pass

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
                namespace=namespace.id,
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
                        'type': 'none',
                    },
                    'allInOne': {
                        'enabled': True,
                        'ingress': {
                            'enabled': False,
                        },
                    },
                    'agent':{ 'enabled': False },
                    'collector': { 'enabled': False },
                    'query': { 'enabled': False },
                },
                transformations=[make_service_private],
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    namespace,
                ]
            ),
            )

        ## def replace_namespace(obj, opts):
        ##     if "namespace" in obj["metadata"]:
        ##         obj["metadata"]["namespace"] = namespace.id

        ## jaeger = ConfigFile(
        ##     "jaeger",
        ##     "./operators/jaeger-operator.yaml",
        ##     transformations=[remove_status,replace_namespace],
        ##     opts=ResourceOptions(
        ##         parent=self,
        ##         depends_on=[namespace, certmanager],
        ##     )
        ## )

