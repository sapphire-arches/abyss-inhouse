#
# Deploys the required Kafka services
#

from storage import StorageSlice
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)

class Kafka(ComponentResource):
    def __init__(self, name: str,
                 opts: ResourceOptions = None):
        super().__init__('abyss:component:Kafka', name, {}, opts)

        kafka_slice = StorageSlice(
            name="abyss-kafka-primary",
            size="8Gi",
            class_name="abyss-kafka-primary",
            opts=ResourceOptions(parent=self))

        log_slice = StorageSlice(
            name="abyss-kafka-log",
            size="8Gi",
            class_name="abyss-kafka-log",
            opts=ResourceOptions(parent=self))

        zk_slice = StorageSlice(
            name="abyss-zk",
            size="8Gi",
            class_name="abyss-zk",
            opts=ResourceOptions(parent=self))

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
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    zk_slice, log_slice, kafka_slice
                ]
            ))

        self.register_outputs({})


