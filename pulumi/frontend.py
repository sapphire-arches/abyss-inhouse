#
# Specification of frontend resources
#
import pulumi
from service_deployment import ServiceDeployment
from config import is_minikube
from pulumi_kubernetes.networking.v1 import Ingress

def build(replicas=1):
    deployment = ServiceDeployment(
        "frontend",
        image="nginx",
        replicas=replicas,
        ports=[80],
        allocate_ip_address=True,
        is_minikube=is_minikube)

    Ingress('frontend',
        metadata={
            'annotations': {
                'kubernetes.io/ingress.class': 'nginx',
            },
        },
        spec={
            'rules': [
                {
                    'host': 'schemaz.cluster.local',
                    'http': {
                        'paths': [{
                            'pathType': 'Prefix',
                            'path': '/',
                            'backend': {
                                'service': {
                                    'name': 'frontend',
                                    'port': { 'number': 80 },
                                },
                            },
                        }],
                    },
                },
            ],
        },
        )

    return deployment
