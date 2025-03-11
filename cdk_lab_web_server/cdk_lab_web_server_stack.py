from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_s3_assets as s3_assets,
    aws_rds as rds
)
from constructs import Construct

class CdkLabWebServerStack(Stack):
    def __init__(self, scope: Construct, id: str,vpc : ec2.Vpc, **kwargs):
        super().__init__(scope, id, **kwargs)

        web_sg = ec2.SecurityGroup(self, "WebServerSG", 
            vpc=vpc, description="Allow HTTP access to web servers", allow_all_outbound=True)
        web_sg.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP from anywhere")
        
        rds_sg = ec2.SecurityGroup(self, "DatabaseSG",
            vpc=vpc, description="Allow MySQL access from web servers", allow_all_outbound=True)
        rds_sg.add_ingress_rule(web_sg, ec2.Port.tcp(3306), "Allow MySQL from web servers")  # web_sg as source&#8203;:contentReference[oaicite:7]{index=7}

        instance_role = iam.Role(self, "WebInstanceRole", 
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com"))

        setup_script_asset = s3_assets.Asset(self, "SetupScriptAsset", path="./cdk_lab_web_server/configure.sh")
        website_asset = s3_assets.Asset(self, "WebsiteZipAsset", path="./static-website.zip")

        setup_script_asset.grant_read(instance_role)
        website_asset.grant_read(instance_role)

        public_subnets = vpc.select_subnets(subnet_type=ec2.SubnetType.PUBLIC).subnets
        for idx, subnet in enumerate(public_subnets):
            instance = ec2.Instance(self, f"WebServer{idx+1}",
                instance_type=ec2.InstanceType("t2.micro"),
                machine_image=ec2.MachineImage.latest_amazon_linux(),  # Amazon Linux 2
                vpc=vpc,
                vpc_subnets=ec2.SubnetSelection(subnets=[subnet]),
                role=instance_role,
                security_group=web_sg
            )
            local_path = instance.user_data.add_s3_download_command(
                bucket=setup_script_asset.bucket, bucket_key=setup_script_asset.s3_object_key
            )
            instance.user_data.add_execute_file_command(file_path=local_path) 
            instance.user_data.add_s3_download_command(
                bucket=website_asset.bucket, bucket_key=website_asset.s3_object_key, local_file="/tmp/website.zip"
            )
            instance.user_data.add_commands("unzip /tmp/website.zip -d /var/www/html/")
        
        db_instance = rds.DatabaseInstance(self, "MyDatabase",
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0_32),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            security_groups=[rds_sg],
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            multi_az=False,
            publicly_accessible=False,
            credentials=rds.Credentials.from_generated_secret("admin"),  # admin username, auto-generated password
            database_name="myappdb"
        )
