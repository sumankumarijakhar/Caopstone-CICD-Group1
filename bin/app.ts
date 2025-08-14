#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { CapstoneStack } from '../lib/stack';

const app = new cdk.App();
new CapstoneStack(app, 'CapstoneStack', {
  env: {
    // Fill your AWS account and region if you want to pin:
    // account: process.env.CDK_DEFAULT_ACCOUNT,
    // region: process.env.CDK_DEFAULT_REGION
  }
});
