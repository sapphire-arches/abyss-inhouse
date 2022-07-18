#
# Common interface for spinning up storage
#

from typing import Sequence

import pulumi
from pulumi import ResourceOptions, ComponentResource, Output
from pulumi_kubernetes.core.v1 import (
    PersistentVolume,
    PersistentVolumeSpecArgs,
    PersistentVolumeClaim,
    PersistentVolumeClaimSpecArgs,
)
from pulumi_kubernetes.meta.v1 import LabelSelectorArgs, ObjectMetaArgs

def get_local_path(name):
    """ Get a local path to mount the DB in, development only! """
    import pathlib
    import os

    assert(pulumi.get_stack() == 'dev')

    local_path = pathlib.Path(__file__)
    database_path = local_path.parent.parent.absolute().joinpath('pv').joinpath(name)

    if not pulumi.runtime.is_dry_run():
        database_path.mkdir(mode=0o777, parents=True, exist_ok=True)

    return str(database_path)

def make_volume(name: str, size: str, class_name: str, opts: ResourceOptions):
    labels = {"app": name}
    metadata = ObjectMetaArgs(labels=labels)

    return PersistentVolume(
        name,
        metadata=metadata,
        spec=PersistentVolumeSpecArgs(
            storage_class_name=class_name,
            access_modes=[
                "ReadWriteOnce",
            ],
            # TODO: implement this for non-dev envs
            capacity={
                "storage": size
            },
            local={
                "path": get_local_path(name),
            },
            node_affinity={
                "required": {
                    "node_selector_terms": [{
                        "match_expressions": [{
                            "key": "kubernetes.io/hostname",
                            "operator": "In",
                            "values": [
                                "carrot-cake"
                            ]
                        }],
                        "match_fields": [],
                    }],
                },
            }),
        opts=opts)

class StorageSlice(ComponentResource):
    volume: PersistentVolume
    claim: PersistentVolumeClaim

    def __init__(self, name: str, size: str, class_name: str,
                 opts: ResourceOptions = None):
        super().__init__('abyss:component:StorageSlice', name, {}, opts)

        labels = {"app": name}
        metadata = ObjectMetaArgs(labels=labels)
        # TODO: this is dev-only for now
        self.volume = make_volume(name, size, class_name,
                ResourceOptions(parent=self))

        self.claim = PersistentVolumeClaim(
            name,
            metadata=metadata,
            spec = PersistentVolumeClaimSpecArgs (
                storage_class_name=class_name,
                access_modes = [ "ReadWriteOnce" ],
                resources = {
                    "requests": {
                        "storage": size,
                    }
                },
                volume_name = self.volume.id,
            ),
            opts=ResourceOptions(
                parent=self,
                depends_on=[
                    self.volume
                ]
            ))

        self.register_outputs({})

    def helm_claim(self):
        return self.claim.id.apply(lambda id: id[id.find('/')+1:])
