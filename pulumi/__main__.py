"""A Kubernetes Python Pulumi program"""

import pulumi

stack = pulumi.get_stack()

if stack == 'dev':
    import dev
    dev.build()
elif stack == 'aws':
    import aws
    aws.build()
else:
    raise ValueError(f'Unsupported stack "{stack}"')
