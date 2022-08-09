"""A Kubernetes Python Pulumi program"""

import pulumi

import aws
import dev

stack = pulumi.get_stack()

if stack == 'dev':
    dev.build()
elif stack == 'aws':
    aws.build()
else:
    raise ValueError(f'Unsupported stack "{stack}"')
