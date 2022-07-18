#
# Deploys the required Kafka services
#

from storage import StorageSlice
import pulumi
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_kafka import Provider
from pulumi_kubernetes.core.v1 import (
    Service,
)
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)

class Kafka(ComponentResource):
    provider: Provider

    def __init__(self, name: str,
                 opts: ResourceOptions = None):
        super().__init__('abyss:component:Kafka', name, {}, opts)

        kafka_slice = StorageSlice(
            name=name + "-primary",
            size="8Gi",
            class_name="abyss-kafka-primary",
            opts=ResourceOptions(parent=self))

        log_slice = StorageSlice(
            name=name + "-log",
            size="8Gi",
            class_name="abyss-kafka-log",
            opts=ResourceOptions(parent=self))

        zk_slice = StorageSlice(
            name=name + "-zk",
            size="8Gi",
            class_name="abyss-zk",
            opts=ResourceOptions(parent=self))

        # The actual postgresql server
        chart = Chart(
            name,
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

        service_name = "v1/Service:default/" + name

        chart.resources[service_name].apply(lambda x: print(x))

        kafka_spec = chart.resources[service_name].spec

        def mk_ips(ips, ports):
            for port in ports:
                if port['target_port'] == "kafka-client":
                    break

            if port is None:
                return None

            port = port['port']

            return list(map(lambda i: f"{i}:{port}", ips))

        bootstrap_servers = Output.all(kafka_spec.cluster_ips, kafka_spec.ports) \
            .apply(lambda args: mk_ips(args[0], args[1]))

        self.provider = Provider(name,
            bootstrap_servers=bootstrap_servers,
            opts=ResourceOptions(
                parent=self,
                depends_on=[chart]
            ))

        pulumi.export("kafka-ips", bootstrap_servers)

        self.register_outputs({
            "provider": self.provider
        })


