#
# Deploys the required postgresql database
#
from pulumi_kubernetes.helm.v3 import (
    Chart,
    ChartOpts,
    FetchOpts,
)
from storage import StorageSlice

def build():
    name = "abyss-postgresql"
    size = "10Gi"

    slice = StorageSlice(
        name=name,
        size=size,
        class_name="abyss-pgsql")
    # We need to strip the namespace because the chart logic already prepends it.
    claim_id = slice.claim.id.apply(lambda id: id[id.find('/')+1:])

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
                        "existingClaim": claim_id,
                    }
                }
            }
        ))


