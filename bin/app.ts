#!/usr/bin/env node
import * as cdk from 'aws-cdk-lib';
import { CapstoneStack } from '../lib/stack';

const app = new cdk.App();

new CapstoneStack(app, 'CapstoneStack', {
  // Avoids the hnb659fds bootstrap requirement
  synthesizer: new cdk.LegacyStackSynthesizer(),

  // Optional: pin env if you want
  // env: { account: process.env.CDK_DEFAULT_ACCOUNT, region: process.env.CDK_DEFAULT_REGION }
});
