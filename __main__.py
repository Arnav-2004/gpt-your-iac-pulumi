"""A public-facing Application Load Balancer (ALB) to distribute incoming web traffic."""

import pulumi
import pulumi_aws as aws

stack_name = pulumi.get_stack()
config = pulumi.Config()

vpc = aws.ec2.Vpc(
    f"{stack_name}-vpc",
    cidr_block="10.0.0.0/16",
    enable_dns_hostnames=True,
    enable_dns_support=True,
)

internet_gateway = aws.ec2.InternetGateway(f"{stack_name}-igw", vpc_id=vpc.id)

# attachment = aws.ec2.InternetGatewayAttachment(
#     f"{stack_name}-igw-attachment",
#     vpc_id=vpc.id,
#     internet_gateway_id=internet_gateway.id
# )

public_subnet1 = aws.ec2.Subnet(
    f"{stack_name}-public-subnet1",
    cidr_block="10.0.1.0/24",
    availability_zone="us-east-1a",
    vpc_id=vpc.id,
    map_public_ip_on_launch=True,
)

public_subnet2 = aws.ec2.Subnet(
    f"{stack_name}-public-subnet2",
    cidr_block="10.0.101.0/24",
    availability_zone="us-east-1b",
    vpc_id=vpc.id,
    map_public_ip_on_launch=True,
)

alb_security_group = aws.ec2.SecurityGroup(
    f"{stack_name}-alb-sg",
    vpc_id=vpc.id,
    ingress=[
        {
            "protocol": "tcp",
            "from_port": 80,
            "to_port": 80,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
    egress=[
        {
            "protocol": "-1",
            "from_port": 0,
            "to_port": 0,
            "cidr_blocks": ["0.0.0.0/0"],
        },
    ],
)

alb = aws.lb.LoadBalancer(
    f"{stack_name}-alb",
    internal=False,
    security_groups=[alb_security_group.id],
    subnets=[public_subnet1.id, public_subnet2.id],
)

target_group = aws.lb.TargetGroup(
    f"{stack_name}-target-group",
    port=80,
    protocol="HTTP",
    target_type="instance",
    vpc_id=vpc.id,
    health_check={
        "path": "/",
        "port": "80",
        "protocol": "HTTP",
        "timeout": 5,
        "interval": 30,
        "healthy_threshold": 2,
        "unhealthy_threshold": 2,
    },
)

listener = aws.lb.Listener(
    f"{stack_name}-listener",
    load_balancer_arn=alb.arn,
    port=80,
    default_actions=[
        {
            "type": "forward",
            "target_group_arn": target_group.arn,
        },
    ],
)

pulumi.export("alb_dns_name", alb.dns_name)
