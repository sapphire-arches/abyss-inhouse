#
# Deploys the required Kafka services
#

from storage import StorageSlice
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)

def build():
    kafka_slice = StorageSlice(
        name="abyss-kafka-primary",
        size="8Gi",
        class_name="abyss-kafka-primary")

    log_slice = StorageSlice(
        name="abyss-kafka-log",
        size="8Gi",
        class_name="abyss-kafka-log")

    zk_slice = StorageSlice(
        name="abyss-zk",
        size="8Gi",
        class_name="abyss-zk")

    # The actual postgresql server
    chart = Chart(
        "abyss-kafka",
        ChartOpts(
            chart="kafka",
            version="18.0.3",
            fetch_opts=FetchOpts(
                repo="https://charts.bitnami.com/bitnami",
            ),
            values={
                "persistence": {
                    "existingClaim": kafka_slice.helm_claim(),
                },
                "logPersistence": {
                    "existingClaim": log_slice.helm_claim(),
                },
                "zookeeper": {
                    "persistence": {
                        "existingClaim": zk_slice.helm_claim(),
                    }
                },
            }
        ))


