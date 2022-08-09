import pulumi
import pulumi_kafka
from pulumi import ResourceOptions
from pulumi_kafka import Topic
from pulumi_kubernetes_cert_manager import CertManager

from common.observability import JaegerDeployment
from config import is_minikube

from .database import Database
from .frontend import build as build_frontend
from .ingress import Ingress
from .kafka import Kafka


def build():
    # Make sure we can see what's happening
    ingress = Ingress()
    certmanager = CertManager('cert-manager', install_crds=True)
    # Primary database
    database = Database('db', True, certmanager)
    JaegerDeployment(certmanager, ingress, True)

    # Deploy a kafka cluster
    kafka = Kafka("kafka")

    # Create a topic on the Kafka cluster
    topic_options = ResourceOptions(
        provider=kafka.provider,
        parent=kafka,
    )

    topic = Topic("steam-jobs",
                  partitions=5,
                  replication_factor=1,
                  config={
                      "cleanup.policy": "compact",
                      "segment.ms": "20000",
                  },
                  opts=topic_options)

    pulumi.export('topic.steam-jobs', topic.id)

    # Frontend
    frontend = build_frontend()

    pulumi.export("ip", frontend.ip_address)
