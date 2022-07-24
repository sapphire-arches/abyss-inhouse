#
# Deploys the required postgresql database
#
import base64

import pulumi
from pulumi import ComponentResource
from pulumi import Output
from pulumi import ResourceOptions
from pulumi_kubernetes.core.v1 import Secret
from pulumi_kubernetes.helm.v3 import Chart
from pulumi_kubernetes.helm.v3 import ChartOpts
from pulumi_kubernetes.helm.v3 import FetchOpts
from pulumi_random import RandomPassword

from storage import StorageSlice


class Database(ComponentResource):
    postgres_password: Output[str]

    def __init__(self, name: str, opts: ResourceOptions = None):
        super().__init__('abyss:component:Database', name, {}, opts)
        size = "10Gi"

        slice = StorageSlice(name=name,
                             size=size,
                             class_name="abyss-pgsql",
                             opts=ResourceOptions(parent=self))

        self.postgres_password = RandomPassword(
            name, length=16, opts=ResourceOptions(parent=self)).result

        pulumi.export('postgres-password', self.postgres_password)

        secret = Secret(
            name,
            data={
                'postgres-password':
                self.postgres_password.apply(lambda s: base64.b64encode(
                    s.encode('utf-8')).decode('utf-8')),
            },
            opts=ResourceOptions(parent=self),
        )

        # The actual postgresql server
        chart = Chart(
            name,
            ChartOpts(
                chart="postgresql",
                version="11.6.16",
                fetch_opts=FetchOpts(
                    repo="https://charts.bitnami.com/bitnami", ),
                values={
                    "primary": {
                        "persistence": {
                            "existingClaim": slice.helm_claim(),
                        }
                    },
                    "auth": {
                        "existingSecret":
                        secret.id.apply(lambda id: id[id.find('/') + 1:]),
                    }
                }),
            opts=ResourceOptions(parent=self, depends_on=[slice]))

        self.register_outputs({'postgress_password': self.postgres_password})
