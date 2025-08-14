# Project Report — Capstone CI/CD (Group 1)

**Members:** Preethi Jakhar, Suman Kumari Jakhar  
**Date:** August 14, 2025

## 1. Application & Infrastructure Description
- **Frontend:** Minimal single-page app (HTML/JS) hosted on S3 and served via CloudFront.
- **Backend:** AWS Lambda (Node.js) behind API Gateway, proxy mode.
- **Database:** DynamoDB (PAY_PER_REQUEST). Partition key: `id`.
- **IaC:** AWS CDK (TypeScript) provisions all resources + CloudWatch dashboard.
- **Routing:** CloudFront routes `/api/*` to API Gateway origin; no CORS needed.

## 2. Pipeline Design
- **Tool:** GitHub Actions (CI + Deploy + CodeQL).
- **Stages:**
  1. **Source:** GitHub repo with protected `main` and feature branches.
  2. **Code Scanning (bonus):** CodeQL workflow on PRs + schedule.
  3. **Build:** TypeScript compile of CDK + handler; `npm run build`.
  4. **Test:** Jest unit tests (≥5) with coverage; CI prints coverage.
  5. **Deploy:** CDK deploy using AWS OIDC, no static AWS keys.
- **Triggers:** On PRs (CI) and on push to `main` (deploy).

## 3. Branching & Collaboration
- Strategy: `main` protected; feature branches per person.
- PRs: Minimum 5 with reviews + screenshots included in submission.
- Code Reviews: Each member reviews the other's PRs.

## 4. Monitoring & Logging
- **CloudWatch Logs:** Lambda logs for troubleshooting.
- **Dashboard:** Shows API 5XX, Lambda duration p95, errors/throttles.
- **How to debug:** Use API logs + Lambda logs. Re-run failed deploys from Actions tab.

## 5. Challenges & Resolutions (examples)
- **AWS credentials:** Solved via GitHub OIDC role (no local keys).
- **CORS issues:** Bypassed by routing `/api/*` through CloudFront to API Gateway.
- **Minimal code vs. requirements:** Kept frontend static, moved logic to Lambda; tests focus on core helpers.

## 6. How to Reproduce
1. Create OIDC role using `iam/github-oidc-role.yaml` (CloudFormation).
2. Set `AWS_DEPLOY_ROLE_ARN` repository variable.
3. Push to `main`. Wait for deploy to finish.
4. Open `SiteUrl` output; test UI.

## 7. Screenshots to include
- GitHub PRs & reviews, CodeQL results, Actions runs.
- CloudFormation stacks, API Gateway, Lambda, DynamoDB, CloudFront.
- CloudWatch dashboard, working web app.
