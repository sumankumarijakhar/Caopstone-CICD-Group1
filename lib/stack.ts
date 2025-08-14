import * as cdk from 'aws-cdk-lib';
import { Duration, Stack, StackProps, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

export class CapstoneStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // DynamoDB table
    const table = new dynamodb.Table(this, 'ItemsTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST
    });

    // Inline Lambda code (no backticks, no bundling)
    const inlineCode =
      'const AWS = require("aws-sdk");\n' +
      'const ddb = new AWS.DynamoDB.DocumentClient();\n' +
      'const TABLE = process.env.TABLE_NAME;\n' +
      'const json = (statusCode, body) => ({ statusCode, headers: { "Content-Type":"application/json" }, body: JSON.stringify(body) });\n' +
      'exports.handler = async (event) => {\n' +
      '  const path = (event && (event.path || event.rawPath || (event.requestContext && event.requestContext.http && event.requestContext.http.path))) || "";\n' +
      '  const method = (event && (event.httpMethod || (event.requestContext && event.requestContext.http && event.requestContext.http.method))) || "GET";\n' +
      '  if (path.endsWith("/health") && method === "GET") return json(200, { ok: true });\n' +
      '  if (path.endsWith("/items") && method === "GET") { const data = await ddb.scan({ TableName: TABLE, Limit: 50 }).promise(); return json(200, { items: data.Items || [] }); }\n' +
      '  if (path.endsWith("/items") && method === "POST") { let body={}; try{ body = JSON.parse(event.body || "{}"); }catch{} if(!body.id || !body.title) return json(400,{ error:"id and title required"}); await ddb.put({ TableName: TABLE, Item: body }).promise(); return json(201,{ saved:true, item: body }); }\n' +
      '  return json(404, { error: "Not found" });\n' +
      '};\n';

    // Lambda (Node 16 includes aws-sdk v2)
    const fn = new lambda.Function(this, 'ApiFunction', {
      runtime: lambda.Runtime.NODEJS_16_X,
      handler: 'index.handler',
      timeout: Duration.seconds(10),
      memorySize: 256,
      environment: { TABLE_NAME: table.tableName },
      code: lambda.Code.fromInline(inlineCode)
    });
    table.grantReadWriteData(fn);

    // Public Lambda Function URL (no auth)
    const fnUrl = fn.addFunctionUrl({
      authType: lambda.FunctionUrlAuthType.NONE
    });

    // S3 for frontend
    const siteBucket = new s3.Bucket(this, 'SiteBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true
    });

    // CloudFront distribution: S3 default; /api/* → Lambda Function URL
    const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
      defaultRootObject: 'index.html',
      defaultBehavior: {
        origin: new origins.S3Origin(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED
      }
    });

    // Extract the domain from the function URL for HttpOrigin
    const fnDomain = cdk.Fn.select(2, cdk.Fn.split('/', fnUrl.url));
    distribution.addBehavior(
      '/api/*',
      new origins.HttpOrigin(fnDomain),
      {
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER
      }
    );

    // CloudWatch dashboard (Lambda metrics)
    const dash = new cloudwatch.Dashboard(this, 'Dashboard', {
      dashboardName: 'Capstone-Observability'
    });
    dash.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'Lambda Invocations',
        left: [fn.metricInvocations({ period: Duration.minutes(1), statistic: 'Sum' })]
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Errors & Throttles',
        left: [
          fn.metricErrors({ period: Duration.minutes(1), statistic: 'Sum' }),
          fn.metricThrottles({ period: Duration.minutes(1), statistic: 'Sum' })
        ]
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration (p95)',
        left: [fn.metricDuration({ period: Duration.minutes(1), statistic: 'p95' })]
      })
    );

    // Outputs
    new CfnOutput(this, 'FunctionUrl', { value: fnUrl.url });
    new CfnOutput(this, 'SiteUrl', { value: 'https://' + distribution.domainName });
    new CfnOutput(this, 'TableName', { value: table.tableName });
    new CfnOutput(this, 'SiteBucketName', { value: siteBucket.bucketName });
    new CfnOutput(this, 'DistributionId', { value: distribution.distributionId });
  }
}
