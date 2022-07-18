#
# Specification of frontend resources
#
import pulumi
from service_deployment import ServiceDeployment
from config import is_minikube

def build(replicas=1):
    return ServiceDeployment(
        "frontend",
        image="nginx",
        replicas=replicas,
        ports=[80],
        allocate_ip_address=True,
        is_minikube=is_minikube)
