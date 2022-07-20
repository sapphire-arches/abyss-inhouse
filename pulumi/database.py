#
# Deploys the required postgresql database
#
import pulumi
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_random import RandomPassword
from pulumi_kubernetes.core.v1 import (
    Secret,
)
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)
from storage import StorageSlice

class Database(ComponentResource):
    postgres_password: Output[str]

    def __init__(self, name: str, opts: ResourceOptions =  None):
        super().__init__('abyss:component:Database', name, {}, opts)
        size = "10Gi"

        slice = StorageSlice(
            name=name,
            size=size,
            class_name="abyss-pgsql",
            opts=ResourceOptions(parent=self))

        self.postgres_password = RandomPassword(name, length=16)

        secret = Secret(
            name,
            data={
                'postgres-password': self.postgres_password,
            },
            opts=ResourceOptions(parent=self),
            )

        # The actual postgresql server
        # TODO: feed the chart a secret we generate to get better integration
        chart = Chart(
            name,
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
                    },
                    "auth": {
                        "existingSecret": secret.id,
                    }
                }
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    slice
                ]
            ))

        self.register_outputs({
            'postgress_password': self.postgres_password
        })
