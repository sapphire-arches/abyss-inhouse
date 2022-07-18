"""A Kubernetes Python Pulumi program"""

import pulumi
import pulumi_kafka
from config import is_minikube

# Deploy a kafka cluster

# Create a topic on the Kafka cluster
import kafka
kafka = kafka.build()
# topic = kafka.Topic(
#     "steam-jobs",
#     partitions=1,
#     replication_factor=1,
#     Frontend service

# Primary database
import database
database = database.build()

# Frontend
import frontend
frontend = frontend.build()

pulumi.export("ip", frontend.ip_address)
