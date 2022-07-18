"""A Kubernetes Python Pulumi program"""

import pulumi
import pulumi_kafka
from config import is_minikube
from database import Database
from kafka import Kafka

# Deploy a kafka cluster
kafka = Kafka("abyss-kafka")

# Create a topic on the Kafka cluster
# topic = kafka.Topic(
#     "steam-jobs",
#     partitions=1,
#     replication_factor=1,
#     Frontend service

# Primary database
database = Database("abyss-db")

# Frontend
import frontend
frontend = frontend.build()

pulumi.export("ip", frontend.ip_address)
