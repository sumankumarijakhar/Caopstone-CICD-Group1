# 10-Min Demo Script (No Slides)

> Tip: rehearse once — this fits in 8–10 min.

**0:00 — 0:45 Intro**
- Team: Preethi Jakhar & Suman Kumari Jakhar.
- Goal: End-to-end CI/CD with minimal code, enterprise practices.

**0:45 — 2:00 Repo & Branching**
- Show repo layout (frontend/backend/CDK, workflows).
- Show branch protection and 5+ PRs with reviews per member.

**2:00 — 4:30 CI/CD**
- Open Actions → show CI run on PR (build, tests, coverage, synth).
- Open CodeQL → show security scan results.
- Open Deploy workflow → show successful deployment and CDK outputs.

**4:30 — 7:30 Live App**
- Open `SiteUrl` (CloudFront).
- Click **Health** → OK.
- Add an item `{ id, title }` → created.
- Refresh → items listed (DynamoDB).
- Open CloudWatch Logs (Lambda) briefly to show traces.
- Show CloudWatch Dashboard: API 5xx (likely 0), Lambda p95, errors/throttles.

**7:30 — 9:30 IaC**
- Open CloudFormation → show stacks/resources.
- Open CDK code (`lib/stack.ts`) and Lambda (`backend/handler.ts`), <30 seconds each.
- Emphasize OIDC (no static keys) and immutable infra.

**9:30 — 10:00 Close**
- Summarize: All requirements met, extensible for future.
