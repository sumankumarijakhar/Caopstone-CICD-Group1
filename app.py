#!/usr/bin/env python3
import aws_cdk as cdk
from stacks.capstone_stack import CapstoneStack

app = cdk.App()
CapstoneStack(app, "CapstoneStack", synthesizer=cdk.LegacyStackSynthesizer())
app.synth()
