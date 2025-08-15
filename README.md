# Capstone – Group 1 (Python Serverless CI/CD)

**Team:** Preethi Jakhar & Suman Kumari Jakhar  
**Goal:** Build a small web app + **full CI/CD pipeline** that deploys to AWS with **Infrastructure as Code** and **monitoring**.

---

## 1) What we built (short)

A tiny **to-do/items** app:

- **Frontend:** static site (HTML/JS/CSS) hosted on **S3** and served through **CloudFront**.
- **Backend API:** **AWS Lambda (Python)** exposed using a **Function URL**.
- **Data “DB”:** a JSON file `data/items.json` stored in the same S3 bucket.

We used **AWS CDK (Python)** to create all cloud resources, and **GitHub Actions** to test and deploy automatically on every push to `main`.

---

## 2) Architecture (how it flows)

```
Browser
   │
   ├─ (GET) https://<cloudfront-domain>          ->  CloudFront  -> S3 (frontend files)
   │
   └─ (GET/POST/PUT/DELETE) /api/*               ->  CloudFront  -> Lambda Function URL (Python)
                                                       │
                                                       └─ read/write  data/items.json  in S3
```

- We also send **custom metrics** from Lambda to **CloudWatch** (Requests, Errors, LatencyMs).


## 3) What the app can do

- Health check: `GET /api/health` → `{ "ok": true }`
- Stats: `GET /api/stats` → item count
- List items: `GET /api/items`
- Add item: `POST /api/items` (needs `{ "id": "...", "title": "..." }`)
- Get one: `GET /api/items/<id>`
- Update: `PUT /api/items/<id>` (body: `{ "title": "..." }`)
- Delete: `DELETE /api/items/<id>`

> If you POST an existing `id` the API returns **409 Conflict** (it means “already exists”).

---

## 4) Repo layout (important folders)

```
frontend/            # index.html, app.js, styles.css
lambda/              # handler.py (entry), logic.py (routing/validation)
stacks/              # CDK stack definition (S3, CloudFront, Lambda URL, Dashboard)
.github/workflows/   # CI pipeline (tests) and CD pipeline (deploy)
tests/               # pytest unit tests for backend (>=5 tests + coverage)
cdk.json             # CDK context (includes lambdaExecRoleArn)
requirements.txt     # Python deps for CDK/Lambda
```

---

## 5) CI/CD pipeline (GitHub Actions)

**Two workflows:**

1) **CI (tests + coverage + cdk synth)** runs on pull requests  
   - Installs deps  
   - Runs `pytest --cov` (we show coverage in the job logs)  
   - Runs `cdk synth` to validate the IaC

2) **Deploy** runs on pushes to `main`  
   - Configures **AWS credentials** using the **temporary sandbox keys**  
   - `cdk bootstrap` (idempotent) and `cdk deploy`  
   - Uploads `/frontend` to S3 and **invalidates CloudFront** cache

**Automated triggers:** PRs run CI; merging to `main` runs deploy automatically.

---

## 6) Secrets needed (for the sandbox)

Create these **repository secrets** in GitHub → *Settings → Secrets → Actions*:

- `AWS_ACCESS_KEY_ID`  
- `AWS_SECRET_ACCESS_KEY`  
- `AWS_SESSION_TOKEN`  (⚠️ sandbox tokens **expire**, refresh when needed)
- `AWS_REGION` (e.g. `us-east-1`)

We also set the existing Lambda role in `cdk.json`:

```json
{
  "app": "python app.py",
  "context": {
    "lambdaExecRoleArn": "arn:aws:iam::<ACCOUNT_ID>:role/lambda-run-role"
  }
}
```

## 7) How to deploy (quick)

1. Push to the **`main`** branch.  
2. Wait for the **Deploy** workflow to finish (green).  
3. In **CloudFormation outputs** you will see:
   - `SiteUrl` → open this URL in your browser (CloudFront)  
   - `SiteBucketName` → S3 bucket name
   - `DistributionId` → CloudFront distribution ID

Try the site:
- Health → `{ "ok": true }`
- Add an item → Refresh → see it in the list
- Edit title → **Save**
- Delete → Refresh

---

## 8) Run tests locally

```bash
python -m venv .venv && source .venv/bin/activate  # (Windows: .venv\Scripts\activate)
pip install -r requirements.txt
pytest -q --cov
```

---

## 9) Monitoring & logs

- **CloudWatch Metrics (namespace `Capstone/App`):** Requests, Errors, LatencyMs (via Embedded Metric Format).
- **CloudWatch Dashboard:** shows invocations, errors and duration.
- **Logs:** Lambda logs (JSON lines) with the same metrics and errors.

---


## 10) Branching + code reviews (what we practiced)

- One protected branch: **`main`**  
- Each of us used **feature branches** (e.g., `preethi/frontend-edit`, `suman/lambda-crud`)  
- Opened **Pull Requests** for every change (at least 5 PRs total)  
- Each PR had a reviewer from the teammate and ran the CI tests before merge

> Keep screenshots of PRs + green checks for your submission.

---

## 11) Demo script (10 minutes, no slides)

1. **GitHub Actions**: show the latest CI (tests + coverage) and Deploy run.  
2. **CloudFormation**: show stack resources created by CDK.  
3. **Open SiteUrl**:
   - Click **Health** → `{ "ok": true }`
   - Add item → Refresh → item appears
   - Edit title (Save) → Refresh  
   - Delete → Refresh
4. **S3 console**: open `data/items.json` to show the stored data.  
5. **CloudWatch**: open dashboard → show invocations/errors/latency moving.  
6. **(If time)** open Lambda logs → show a JSON line with `Operation`, `Requests`, `Errors`, `LatencyMs`.

---

## 12) What we learned / challenges

- Working inside a **restricted sandbox** (no new IAM roles) → solved with **bucket policy** and a **pre-existing role**.
- Full **CI/CD** with automatic deploys gave us repeatable environments.
- Using **CDK** kept our infrastructure versioned and easy to change.

---
