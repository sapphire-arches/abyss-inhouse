#
# Loads some common config options from the Pulumi config store
#
import pulumi

config = pulumi.Config()

is_minikube = config.require_bool("isMinikube")

__all__ = ["is_minikube", "namespace"]
