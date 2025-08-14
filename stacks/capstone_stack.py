import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    Stack, Duration, CfnOutput,
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_dynamodb as dynamodb,
    aws_lambda as lambda_,
    aws_cloudwatch as cloudwatch,
)

class CapstoneStack(Stack):
    """Infra: DynamoDB + Lambda (Function URL) + S3 + CloudFront + Dashboard.
    Uses LegacyStackSynthesizer to avoid CDK bootstrap & ECR.
    CloudFront uses an Origin Access Identity (OAI) to read from a private S3 bucket.
    """
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # ---------- Database ----------
        table = dynamodb.Table(
            self, "ItemsTable",
            partition_key=dynamodb.Attribute(name="id", type=dynamodb.AttributeType.STRING),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )

        # ---------- Lambda (inline code built by concatenating logic + handler) ----------
        with open("lambda/logic.py", "r", encoding="utf-8") as f:
            logic_src = f.read()
        with open("lambda/handler.py", "r", encoding="utf-8") as f:
            handler_src = f.read()

        # Remove the import when we inline both files together
        handler_src = handler_src.replace("from logic import route, parse_body, validate_item  # used locally; inlined at deploy", "")
        handler_src = handler_src.replace("from logic import route, parse_body, validate_item", "")

        inline_code = f"{logic_src}\n\n{handler_src}"

        fn = lambda_.Function(
            self, "ApiFunction",
            runtime=lambda_.Runtime.PYTHON_3_12,
            handler="index.handler",
            timeout=Duration.seconds(10),
            memory_size=256,
            environment={"TABLE_NAME": table.table_name},
            code=lambda_.Code.from_inline(inline_code),
        )
        table.grant_read_write_data(fn)

        # Public Lambda Function URL (no auth). CloudFront proxies /api/* to this.
        fn_url = fn.add_function_url(auth_type=lambda_.FunctionUrlAuthType.NONE)

        # ---------- Frontend ----------
        site_bucket = s3.Bucket(
            self, "SiteBucket",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            versioned=True,
        )

        # CloudFront OAI for private bucket access
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

        # Route /api/* to the Lambda Function URL (domain only; no path)
        fn_domain = cdk.Fn.select(2, cdk.Fn.split("/", fn_url.url))
        distribution.add_behavior(
            "/api/*",
            origin=origins.HttpOrigin(fn_domain),
            allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
            cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
            origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        )

        # ---------- Monitoring ----------
        dash = cloudwatch.Dashboard(self, "Dashboard", dashboard_name="Capstone-Observability")
        dash.add_widgets(
            cloudwatch.GraphWidget(
                title="Lambda Invocations",
                left=[fn.metric_invocations(period=Duration.minutes(1), statistic="Sum")],
            ),
            cloudwatch.GraphWidget(
                title="Lambda Errors & Throttles",
                left=[
                    fn.metric_errors(period=Duration.minutes(1), statistic="Sum"),
                    fn.metric_throttles(period=Duration.minutes(1), statistic="Sum"),
                ],
            ),
            cloudwatch.GraphWidget(
                title="Lambda Duration (p95)",
                left=[fn.metric_duration(period=Duration.minutes(1), statistic="p95")],
            ),
        )

        # ---------- Outputs ----------
        CfnOutput(self, "FunctionUrl", value=fn_url.url)
        CfnOutput(self, "SiteUrl", value="https://" + distribution.domain_name)
        CfnOutput(self, "TableName", value=table.table_name)
        CfnOutput(self, "SiteBucketName", value=site_bucket.bucket_name)
        CfnOutput(self, "DistributionId", value=distribution.distribution_id)
