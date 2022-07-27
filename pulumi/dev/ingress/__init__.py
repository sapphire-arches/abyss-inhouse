#
# ingress logic for local clusters
#
# This gets super complicated because k8s doesn't ship with a default
# implementation of LoadBalancers, so we need to spin up a MetalLB instance
#
import pulumi
from pulumi import ComponentResource
from pulumi import Output
from pulumi import ResourceOptions
from pulumi_kubernetes.apiextensions import CustomResource
from pulumi_kubernetes.helm.v3 import Chart
from pulumi_kubernetes.helm.v3 import ChartOpts
from pulumi_kubernetes.helm.v3 import FetchOpts
from pulumi_kubernetes.yaml import ConfigGroup
from pulumi_kubernetes_ingress_nginx import ControllerArgs
from pulumi_kubernetes_ingress_nginx import ControllerPublishServiceArgs
from pulumi_kubernetes_ingress_nginx import ControllerServiceArgs
from pulumi_kubernetes_ingress_nginx import IngressController

from transformers import remove_status


class MetalLB(ComponentResource):

    def __init__(self, opts: ResourceOptions = None):
        super().__init__('abyss:component:MetalLB', 'metallb', {}, opts)

        chart = Chart('metallb',
                      ChartOpts(
                          chart='metallb',
                          version='v0.13.3',
                          fetch_opts=FetchOpts(
                              repo='https://metallb.github.io/metallb', ),
                          transformations=[
                              remove_status,
                          ],
                      ),
                      opts=ResourceOptions(parent=self, ))

        ip_address_pool = chart.resources[
            'apiextensions.k8s.io/v1/CustomResourceDefinition:ipaddresspools.metallb.io']

        ips = ConfigGroup('metallb',
                          yaml=[
                              '''
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: metallb-config
  namespace: default
spec:
  addresses:
  - 192.168.10.0/24
'''
                          ],
                          opts=ResourceOptions(
                              parent=self,
                              depends_on=[chart, ip_address_pool],
                          ))


class Ingress(ComponentResource):

    def __init__(self, opts: ResourceOptions = None):
        super().__init__('abyss:component:Ingress', 'ingress', {}, opts)

        lb = MetalLB(opts=ResourceOptions(parent=self))

        # Spin up an nginx ingress controller
        ctrl = IngressController(
            'ingress',
            controller=ControllerArgs(
                publish_service=ControllerPublishServiceArgs(
                    enabled=True, ), ),
            opts=ResourceOptions(parent=self, depends_on=[lb]),
        )
