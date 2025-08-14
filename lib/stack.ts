import * as path from 'path';
import { Duration, Stack, StackProps, CfnOutput } from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as lambdaNode from 'aws-cdk-lib/aws-lambda-nodejs';
import * as apigw from 'aws-cdk-lib/aws-apigateway';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';

export class CapstoneStack extends Stack {
  constructor(scope: Construct, id: string, props?: StackProps) {
    super(scope, id, props);

    // DynamoDB
    const table = new dynamodb.Table(this, 'ItemsTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      removalPolicy: undefined // default RETAIN for safety in class demo
    });

    // Lambda (bundled with esbuild)
    const fn = new lambdaNode.NodejsFunction(this, 'ApiFunction', {
      entry: path.join(__dirname, '..', 'backend', 'handler.ts'),
      runtime: lambda.Runtime.NODEJS_20_X,
      memorySize: 256,
      timeout: Duration.seconds(10),
      bundling: { minify: true, target: 'node20' },
      environment: {
        TABLE_NAME: table.tableName
      }
    });
    table.grantReadWriteData(fn);

    // API Gateway (REST) with Lambda proxy
    const api = new apigw.LambdaRestApi(this, 'ApiGateway', {
      handler: fn,
      proxy: true,
      deployOptions: { stageName: 'prod' }
    });

    // S3 bucket for frontend
    const siteBucket = new s3.Bucket(this, 'SiteBucket', {
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true
    });

    // CloudFront with two origins: S3 (default) and API Gateway (/api/*)
    const distribution = new cloudfront.Distribution(this, 'SiteDistribution', {
      defaultRootObject: 'index.html',
      defaultBehavior: {
        origin: new origins.S3Origin(siteBucket),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED
      }
    });

    // Route /api/* to API Gateway domain (no CORS needed via CF)
    const apiDomain = `${api.restApiId}.execute-api.${Stack.of(this).region}.amazonaws.com`;
    distribution.addBehavior('/api/*',
      new origins.HttpOrigin(apiDomain, { originPath: `/${api.deploymentStage.stageName}` }),
      {
        allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
        cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER
      }
    );

    // Deploy static frontend to S3 and invalidate CF
    new s3deploy.BucketDeployment(this, 'DeployWebsite', {
      destinationBucket: siteBucket,
      sources: [s3deploy.Source.asset(path.join(__dirname, '..', 'frontend'))],
      distribution,
      distributionPaths: ['/*']
    });

    // CloudWatch dashboard
    const dash = new cloudwatch.Dashboard(this, 'Dashboard', {
      dashboardName: 'Capstone-Observability'
    });
    dash.addWidgets(
      new cloudwatch.GraphWidget({
        title: 'API 5XX Errors',
        left: [
          api.metricServerError({ period: Duration.minutes(1), statistic: 'Sum' })
        ]
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Duration (p95)',
        left: [
          fn.metricDuration({ period: Duration.minutes(1), statistic: 'p95' })
        ]
      }),
      new cloudwatch.GraphWidget({
        title: 'Lambda Errors & Throttles',
        left: [
          fn.metricErrors({ period: Duration.minutes(1), statistic: 'Sum' }),
          fn.metricThrottles({ period: Duration.minutes(1), statistic: 'Sum' })
        ]
      })
    );

    new CfnOutput(this, 'ApiUrl', { value: api.url });
    new CfnOutput(this, 'SiteUrl', { value: 'https://' + distribution.domainName });
    new CfnOutput(this, 'TableName', { value: table.tableName });
  }
}
