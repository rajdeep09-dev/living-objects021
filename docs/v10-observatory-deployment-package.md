# BEAST v10 Observatory Deployment Package

> **Status on 2026-08-17:** The authenticated observatory has a tested, production-buildable real-data evidence route. It has **no public Observatory URL** and **no continuous evolution worker**. The managed development preview is not a public deployment.

## What has been prepared and verified locally

The deployable observatory application is located at `/home/ubuntu/living-objects-platform-ui`. Its authenticated `organisms.v9ObservatoryEvidence` route exposes only the artifact-backed record in `server/evidence/v9-observatory-evidence.json`, guarded by `server/v9ObservatoryEvidence.ts`. The displayed values are not generated in the browser and do not start evolutionary work.

The v10 status row is rendered in `client/src/components/V9EvidencePanel.tsx`. It visibly reports the following deployed-state facts:

| Operational property | Verified v10 state | Meaning |
|---|---|---|
| Public Observatory URL | `NOT_DEPLOYED` | No public URL has been assigned or represented as live. |
| Current access | Managed development preview only | The preview is a development environment, not a public service. |
| Continuous evolution worker | `NOT_CONFIGURED` | No background process is attached to the UI. |
| Deployment authorization | `PENDING_EXPLICIT_OWNER_AUTHORIZATION` | Publishing remains an owner-controlled action. |
| 100,000-generation campaign | Not launched | The panel cannot queue, start, or imply this campaign. |

The persisted evidence records SDK version `0.3.0`, the five-stage curriculum contract, the signed local discovery-exchange boundary, the 1,731-case collection count, the retained clean-sorting negative result, and the five eligible Manhattan records. The count is a **parameterized collected-case count**, not a count of distinct test functions.

## Local verification record

The following commands were run on 2026-08-17 after the v10 disclosure was added:

```bash
cd /home/ubuntu/living-objects-platform-ui
pnpm test -- --run \
  server/v9ObservatoryEvidence.test.ts \
  server/v10OperationalStatusRender.test.ts \
  client/src/components/V9EvidencePanel.test.tsx
pnpm build
```

The project test command executed **13 test files and 21 tests**, all passing. The production build completed successfully. Desktop (`1280×720`) and mobile (`375×812`) full-page renders were inspected after the disclosure was introduced; the mobile status grid resolves to two columns without an observed overflow.

## Owner-controlled publication handoff

1. Re-run the commands in the local verification record from the observatory project directory.
2. Confirm that the persisted evidence file still represents the intended engine artifact versions and limits.
3. Save a project checkpoint so the exact tested source is recoverable.
4. If and only if the owner wants public hosting, use the project interface’s **Publish** control and configure a domain there.
5. After publication, test the assigned URL with a new session and verify that authentication and evidence boundaries behave as intended.
6. Amend `server/evidence/v9-observatory-evidence.json`, the visible status row, and this record only after an actual public URL and service configuration have been independently verified.

## Explicit exclusions

This package does **not** publish the application, assign a domain, expose an unauthenticated public URL, deploy a durable worker, create a scheduler, execute a 100,000-generation campaign, submit a paper, or publish a PyPI package. Each of those actions has a separate owner authorization and verification requirement.

## Relevant source and test files

| Purpose | Path |
|---|---|
| Persisted real-data evidence | `living-objects-platform-ui/server/evidence/v9-observatory-evidence.json` |
| Runtime schema guard | `living-objects-platform-ui/server/v9ObservatoryEvidence.ts` |
| Visible authenticated status row | `living-objects-platform-ui/client/src/components/V9EvidencePanel.tsx` |
| Server contract regression | `living-objects-platform-ui/server/v9ObservatoryEvidence.test.ts` |
| Rendered v10 disclosure regression | `living-objects-platform-ui/server/v10OperationalStatusRender.test.ts` |
| Component fixture/render regression | `living-objects-platform-ui/client/src/components/V9EvidencePanel.test.tsx` |
