# Going live

This is a guide, not something already done for you — creating accounts,
pushing to GitHub, and clicking "deploy" on Render/Vercel all need to happen
under *your* accounts. Nothing in this repo talks to any of these services
yet.

**Recommended stack** (free/cheap tiers, minimal ops):
- **Database:** [Neon](https://neon.tech) — serverless Postgres, matches what the handoff doc suggested for Phase 3.
- **Backend services** (Go ingestion-mesh, Python inventory-service, Python notetaker-mcp): [Render](https://render.com) — deploys straight from a `Dockerfile` in your GitHub repo, no local Docker install required (Render builds it remotely).
- **Frontends** (field-app, dashboard): [Vercel](https://vercel.com) — per the handoff doc; builds Next.js natively, no Dockerfile needed.

Dockerfiles for the three backend services are already in the repo
(`ingestion-mesh/Dockerfile`, `inventory-service/Dockerfile`,
`notetaker-mcp/Dockerfile`), plus a `docker-compose.yml` at the repo root
for running the whole backend stack in containers locally (useful to sanity
check before deploying, if you install Docker Desktop — not required for
Render, which builds remotely).

## 0. Push to GitHub

Render and Vercel both deploy from a GitHub repo. If you haven't already:

```
gh repo create <name> --private --source=. --push
```

(or create the repo on github.com and `git remote add origin ... && git push -u origin main`)

## 1. Database (Neon)

1. Create a free Neon project. Copy the connection string it gives you (`postgresql://...`).
2. From your machine (or Neon's SQL editor), apply the schema:
   ```
   psql "<neon-connection-string>" -f inventory-service/db/schema.sql
   ```
3. Seed demo data — **change the demo passwords first** if this will be
   publicly reachable (`inventory-service/db/seed.py` has them in plain
   sight in the repo):
   ```
   cd inventory-service && source .venv/bin/activate
   DATABASE_URL="<neon-connection-string>" python -m db.seed
   ```

## 2. Backend services (Render)

Create three **Web Services** on Render, each pointing at this GitHub repo:

| Service | Dockerfile path | Docker build context | Port |
|---|---|---|---|
| ingestion-mesh | `ingestion-mesh/Dockerfile` | `ingestion-mesh` | 8080 |
| inventory-service | `inventory-service/Dockerfile` | `inventory-service` | 8001 |
| notetaker-mcp | `notetaker-mcp/Dockerfile` | **repo root** (`.`) — it needs `docs/runbooks` too | 8000 |

Environment variables to set per service:

**inventory-service**
- `DATABASE_URL` = your Neon connection string
- `JWT_SECRET` = a real random secret, e.g. `openssl rand -hex 32` — **not** the `dev-secret-change-me...` default

**notetaker-mcp**
- `GEMINI_API_KEY` = your key (omit to run on the deterministic mock instead)
- `INVENTORY_SERVICE_URL` = the inventory-service's Render URL
- `INGESTION_MESH_URL` = the ingestion-mesh's Render URL
- `FIELD_SERVICE_USERNAME` / `FIELD_SERVICE_PASSWORD` = must match a seeded field_tech account (defaults match the seed script)
- `ALLOWED_ORIGIN_REGEX` = a regex matching your deployed frontend origin(s), e.g. `https://.*\.vercel\.app` — **the field-app calls this service directly from the browser**, so this has to be right or it'll be silently CORS-blocked. (The dashboard doesn't need this — it talks to notetaker server-side.)

**ingestion-mesh**
- No required env vars.

Render's free tier spins services down when idle and takes ~30s to wake on
the next request — fine for a portfolio demo, worth knowing if a first
request seems to hang.

## 3. Frontends (Vercel)

Import the repo into Vercel **twice** — once per app, since this is a
monorepo — setting each project's **Root Directory**:

**field-app** (Root Directory: `field-app`)
- `NEXT_PUBLIC_NOTETAKER_URL` = notetaker-mcp's Render URL

**dashboard** (Root Directory: `dashboard`)
- `INGESTION_MESH_URL` = ingestion-mesh's Render URL
- `NOTETAKER_URL` = notetaker-mcp's Render URL
- `INVENTORY_SERVICE_URL` = inventory-service's Render URL

These three are read server-side only (Route Handlers), never sent to the
browser — that's the whole point of the BFF design from Phase 4, see
`dashboard/lib/backend.ts`.

## 4. After first deploy — verify

- Hit each backend's `/health` at its Render URL.
- Open the deployed field-app, submit a note, confirm you get a result back (not a CORS error in devtools — if you do, double check `ALLOWED_ORIGIN_REGEX`).
- Open the deployed dashboard, log in with the seeded admin account, confirm telemetry/inventory populate and the thought log updates after submitting a note.
- Ask the support agent a question — if `GEMINI_API_KEY` wasn't set, you'll get the mock's `[unformatted mock answer...]` output, which is expected, not a bug.

## Things deliberately left for you to decide

- **Custom domains / HTTPS** — Vercel and Render both provision HTTPS automatically on their own subdomains; custom domains are a few clicks in each dashboard if you want one.
- **Kubernetes** — the handoff doc mentions K8s, but for a single-instance portfolio deployment it's meaningfully more operational surface (cluster, ingress, secrets management) for no real benefit over Render's managed containers. The Dockerfiles here would work as-is if you do want to stand up a cluster later (e.g. a k3s box, or a managed cluster on GKE/EKS) — that's a separate, larger task with its own account/billing implications, happy to help if you want to go there.
- **Rotating the demo credentials** (`admin`/`admin-demo-pw`, `field-tech-service`/`field-tech-demo-pw`) — fine for a private demo, not fine if this is going somewhere a stranger could find it.
