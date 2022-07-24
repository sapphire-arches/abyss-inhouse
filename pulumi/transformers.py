def remove_status(obj, opts):
    """ Stupid hack transformer to deal with things that try to set status on
    CRDs """
    if obj["kind"] == "CustomResourceDefinition":
        del obj["status"]

def make_service_private(obj, opts):
    """ Make every service private to the cluster, i.e., turn all services into
    ClusterIP instead of LoadBalancer. """
    if obj["kind"] == "Service" and obj["apiVersion"] == "v1":
        try:
            t = obj["spec"]["type"]
            if t == "LoadBalancer":
                pulumi.info(f'Replacing LB with CIP')
                obj["spec"]["type"] = "ClusterIP"
        except KeyError:
            pass

