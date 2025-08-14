# Capstone Project — Comprehensive CI/CD Pipeline (Group 1)

**Group Members:** Preethi Jakhar, Suman Kumari Jakhar  
**Tech Stack:** AWS CDK (TypeScript), AWS API Gateway + Lambda + DynamoDB, S3 + CloudFront (static frontend), GitHub Actions, CodeQL, CloudWatch

> Goal: Minimal code, maximum marks. End-to-end **build → test/coverage → scan → synth → deploy** using **GitHub Actions** via **AWS OIDC** (no long‑lived AWS keys).

---

## 1) What we built (overview)

- **Frontend:** A tiny single-page web app (vanilla HTML/JS) served from **S3** via **CloudFront**.
- **Backend API:** **AWS Lambda** (Node.js) behind **API Gateway**. Routes:
  - `GET /api/health` (health check)
  - `GET /api/items` (list from DynamoDB)
  - `POST /api/items` (create item: `{ "id": "123", "title": "Task" }`)
- **Database:** **DynamoDB** table with partition key `id`.
- **IaC:** **AWS CDK (TypeScript)** creates all resources + a **CloudWatch Dashboard**.
- **CI/CD:** **GitHub Actions**
  - `ci.yml`: install → build (TypeScript) → unit tests (Jest) → coverage → CDK synth
  - `deploy.yml`: OIDC → CDK deploy on `main`
  - `codeql.yml`: static code scanning (bonus)
- **Branching Strategy:** `main` + feature branches: `feature/preethi-*`, `feature/suman-*`. Always use PRs and code review.

---

## 2) Repository layout

```
.
├─ .github/workflows/
│  ├─ ci.yml
│  ├─ deploy.yml
│  └─ codeql.yml
├─ bin/
│  └─ app.ts
├─ lib/
│  └─ stack.ts
├─ backend/
│  ├─ handler.ts
│  ├─ handler.test.ts
│  └─ jest.config.js
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  └─ styles.css
├─ iam/
│  └─ github-oidc-role.yaml   # one-time role to allow GitHub Actions to deploy
├─ package.json
├─ tsconfig.json
├─ cdk.json
├─ README.md   # (this file)
└─ docs/
   ├─ REPORT.md
   └─ DEMO_SCRIPT.md
```

---

## 3) One-time AWS setup (GitHub OIDC)

1. **Create the OIDC deploy role** in your AWS account (AdministratorAccess for project speed; fine-tune later):
   - Open AWS Console → CloudFormation → **Create stack** → **Upload a template**.
   - Use `iam/github-oidc-role.yaml`.
   - Parameters to replace:
     - **GitHubOrg** → your GitHub org or username (e.g., `your-username`)
     - **GitHubRepo** → the repo name (e.g., `capstone-ci-cd-group1`)
     - **Branch** → `main`
   - After stack finishes, copy the output **`DeployRoleArn`**.

2. **Bootstrap CDK** (first time only) using that role (pipeline will do this automatically if needed):
   - In the `deploy.yml` we run `cdk bootstrap` before `cdk deploy` if the environment is new.

---

## 4) GitHub repository & secrets

- Create a new GitHub repo and push this project.
- In **Actions → Variables** (or **Secrets & variables**):
  - Create **Repository variable** `AWS_DEPLOY_ROLE_ARN` with the **DeployRoleArn** from step 3.

No other secrets or keys are required (thanks to OIDC).

---

## 5) Local quick start (optional)

```bash
# prerequisites: Node.js 20+, npm, AWS account
npm ci
npm run build
npm test  # shows coverage
npm run synth
```

---

## 6) CI/CD

- **Pull Requests** to any branch: `ci.yml` runs build, tests, coverage, `cdk synth` (no deploy).
- **Push to main**: `deploy.yml` assumes `AWS_DEPLOY_ROLE_ARN` and **deploys**:
  - API (API Gateway + Lambda + DynamoDB)
  - Frontend uploaded to S3 and served via CloudFront
  - CloudWatch Dashboard
- **Code Scanning**: `codeql.yml` runs regularly and on PRs.

---

## 7) Using the app after deploy

- GitHub Action outputs CDK stack outputs. Look for:
  - `SiteUrl`: `https://dxxxxxxxx.cloudfront.net`
  - `ApiUrl`: API Gateway base url
- The **frontend** calls API through CloudFront using the path `/api/*`, so just open **SiteUrl** and use the UI.

**Endpoints (via CloudFront):**
- `GET  /api/health`
- `GET  /api/items`
- `POST /api/items`  with JSON: `{ "id": "123", "title": "Buy milk" }`

---

## 8) Branching, commits, and PRs (what to show the professor)

- Branching:
  - `main` (protected)
  - `feature/preethi-add-tests`, `feature/preethi-ui-tweak`, `feature/preethi-docs`, ...
  - `feature/suman-api-fixes`, `feature/suman-coverage`, `feature/suman-monitoring`, ...
- **Each member**: at least **5 commits per component** (frontend/backend/IaC) and **5 PRs** total with reviews.
- Screenshot checklist:
  - Branch protection settings
  - PR list with reviews
  - CodeQL findings (even “0 alerts” is fine)
  - GitHub Actions runs for CI and Deploy
  - CloudFormation stack resources, API Gateway, Lambda, DynamoDB, CloudFront
  - CloudWatch Dashboard & Logs
  - App running (CloudFront URL)

---

## 9) Troubleshooting

- **Deploy fails with permissions** → verify `AWS_DEPLOY_ROLE_ARN` is correct and role trust policy includes your repo/branch.
- **CDK bootstrap missing** → pipeline runs `cdk bootstrap`. Re-run if first attempt timed out.
- **CORS** → Not needed because CloudFront routes `/api/*` to API Gateway—same origin (CloudFront domain).
- **White page** → Wait for CloudFront invalidation (BucketDeployment handles this) or hard refresh.

---

## 10) License
MIT (for coursework)
