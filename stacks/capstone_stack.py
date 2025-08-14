import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack, Duration, CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_lambda as lambda_,
    aws_cloudwatch as cloudwatch,
    aws_iam as iam,
)

class CapstoneStack(Stack):
    """Frontend (S3+CloudFront) + Lambda URL backend + S3 data store.
    Uses EXISTING IAM role (passed via context) to avoid role creation.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # --------- Existing Lambda role (no role creation) ----------
        exec_role_arn = self.node.try_get_context("lambdaExecRoleArn")
        if not exec_role_arn:
            raise ValueError("Missing context: lambdaExecRoleArn")
        exec_role = iam.Role.from_role_arn(self, "ExistingLambdaRole", exec_role_arn, mutable=False)

        # --------- Frontend bucket (private via OAI) ----------
        site_bucket = s3.Bucket(
            self, "SiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
        )
        oai = cloudfront.OriginAccessIdentity(self, "OAI")
        site_bucket.grant_read(oai.grant_principal)

        distribution = cloudfront.Distribution(
            self, "SiteDistribution",
            default_root_object="index.html",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(site_bucket, origin_access_identity=oai),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
            ),
        )

        # Allow Lambda role to read/write our data objects via BUCKET POLICY (no IAM edits)
        site_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                actions=["s3:GetObject", "s3:PutObject"],
                principals=[iam.ArnPrincipal(exec_role_arn)],
                resources=[site_bucket.arn_for_objects("data/*")],
            )
        )

        # --------- Lambda (inline code: logic.py + handler.py) ----------
        with open("lambda/logic.py", "r", encoding="utf-8") as f:
            logic_src = f.read()
        with open("lambda/handler.py", "r", encoding="utf-8") as f:
            handler_src = f.read()
        handler_src = handler_src.replace(
            "from logic import route, parse_body, validate_item  # used locally; inlined at deploy", ""
        ).replace("from logic import route, parse_body, validate_item", "")
        inline_code = f"{logic_src}\n\n{handler_src}"

        fn = lambda_.Function(
            self, "ApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,  # boto3 included
            handler="index.handler",
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={
                "BUCKET_NAME": site_bucket.bucket_name,
                "BUCKET_KEY": "data/items.json",
            },
            code=lambda_.Code.from_inline(inline_code),
            role=exec_role,
        )
        fn_url = fn.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE)

        # Route /api/* via CloudFront → Lambda URL
        fn_domain = cdk.Fn.select(2, cdk.Fn.split("/", fn_url.url))
        distribution.add_behavior(
            "/api/*",
            origin=origins.HttpOrigin(fn_domain),
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )

        # --------- Monitoring ----------
        dash = cloudwatch.Dashboard(self, "Dashboard", dashboard_name="Capstone-Observability")
        dash.add_widgets(
            cloudwatch.GraphWidget(title="Lambda Invocations",
                                   left=[fn.metric_invocations(period=Duration.minutes(1), statistic="Sum")]),
            cloudwatch.GraphWidget(title="Lambda Errors & Throttles",
                                   left=[fn.metric_errors(period=Duration.minutes(1), statistic="Sum"),
                                         fn.metric_throttles(period=Duration.minutes(1), statistic="Sum")]),
            cloudwatch.GraphWidget(title="Lambda Duration (p95)",
                                   left=[fn.metric_duration(period=Duration.minutes(1), statistic="p95")]),
        )

        # --------- Outputs ----------
        CfnOutput(self, "FunctionUrl", value=fn_url.url)
        CfnOutput(self, "SiteUrl", value="https://" + distribution.domain_name)
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
        
