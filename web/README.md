# Living Objects Control Surface

This directory contains the Signal Loom React control surface for the Living Objects production runtime. It is intentionally kept as a standalone frontend so it can be deployed to a static host, served behind the FastAPI control plane, or embedded into an operations portal.

## Local development

From this directory:

```bash
pnpm install
pnpm dev
```

The dashboard currently includes a local simulation mode for deterministic UI exploration. The production wiring point is the FastAPI control plane under `production/api`; set `VITE_API_BASE_URL` in a deployment adapter before enabling authenticated API calls. Do not place secrets in the frontend bundle.

## Runtime controls

The dashboard exposes pause/resume, single-generation stepping, speed, active-species selection, stream visibility, memome browsing, and lineage telemetry. All high-impact controls are deliberately explicit and the visual language reserves copper for intervention, cyan for memory/lineage, and chartreuse for novelty/adaptation.
