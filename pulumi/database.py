#
# Deploys the required postgresql database
#
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)
from storage import StorageSlice

class Database(ComponentResource):
    def __init__(self, name: str, opts: ResourceOptions =  None):
        super().__init__('abyss:component:Kafka', name, {}, opts)
        name = "abyss-postgresql"
        size = "10Gi"

        slice = StorageSlice(
            name=name,
            size=size,
            class_name="abyss-pgsql",
            opts=ResourceOptions(parent=self))

        # The actual postgresql server
        chart = Chart(
            "abyss-pg",
            ChartOpts(
                chart="postgresql",
                version="11.6.16",
                fetch_opts=FetchOpts(
                    repo="https://charts.bitnami.com/bitnami",
                ),
                values={
                    "primary": {
                        "persistence": {
                            "existingClaim": slice.helm_claim(),
                        }
                    }
                }
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    slice
                ]
            ))

        self.register_outputs({})
