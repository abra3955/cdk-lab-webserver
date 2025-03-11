from aws_cdk import (
    Stack,
    App,
    Environment,
    Tags,
    aws_ec2 as ec2
)
from constructs import Construct

class CdkLabNetworkStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)
        
        vpc_name = "MainVPC"
        
        
        self.vpc = ec2.Vpc(
            self, 
            "VPC",  
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"), 
            max_azs=2,  
            
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public", 
                    subnet_type=ec2.SubnetType.PUBLIC,       
                    cidr_mask=24                             
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,  
                    cidr_mask=24
                )
            ],
            
            nat_gateways=2,  
            vpc_name=vpc_name 
        )