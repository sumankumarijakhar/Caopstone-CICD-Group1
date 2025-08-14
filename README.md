# Capstone CI/CD (Python) — Group 1

**Members:** Preethi Jakhar, Suman Kumari Jakhar

**App:** Minimal full‑stack app with a one‑page frontend (CloudFront + S3) and a Python Lambda backend (Lambda **Function URL**) storing items in **DynamoDB**.

**Endpoints** (via CloudFront → Lambda URL):
- `GET /api/health` → `{ "ok": true }`
- `GET /api/items` → list items
- `POST /api/items` → create `{ id, title }`

**Why this design?**
- No API Gateway, no Docker/ECR, no CDK bootstrap → fewer classroom IAM errors.
- Uses `LegacyStackSynthesizer` and **inline Lambda code**, so deploys cleanly.

## Quick start
1. Create a new **GitHub repository** and upload/extract this project.
2. GitHub → **Settings → Secrets and variables → Actions → Secrets** → add:
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_SESSION_TOKEN`
   - (optional) `AWS_REGION` = `us-east-1` (default if omitted)
3. Push to **main** or run **Actions → Deploy (Python) → Run workflow**.
4. After deploy, check **Outputs**:
   - `SiteUrl` → open the app
   - `FunctionUrl` → backend URL (CloudFront proxies `/api/*` to this)
5. On the site, click **Health**, then add an item and **Refresh**.

## Local dev (optional)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pytest --maxfail=1 --disable-warnings -q --cov=lambda --cov-report=term-missing
cdk synth
```

## Repo layout
```
.
├─ app.py
├─ cdk.json
├─ requirements.txt
├─ stacks/
│  └─ capstone_stack.py
├─ lambda/
│  ├─ handler.py
│  └─ logic.py
├─ tests/
│  └─ test_logic.py
├─ frontend/
│  ├─ index.html
│  ├─ app.js
│  └─ styles.css
└─ .github/workflows/
   ├─ ci.yml
   └─ deploy.yml
```
