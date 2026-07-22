<!-- Demo knowledge-base content for the Zenith AI Support Agent (Phase 4.2). Not a real operations manual. -->

# Escalation Policy

## When to escalate immediately
- Any single asset reports `critical` status on more than one metric at
  the same time.
- More than 3 assets at the same location are simultaneously `degraded`
  or `critical`.
- A repeat failure (same asset, same part) within 90 days.
- A field note's telemetry claim contradicts live telemetry (the AI
  notetaker's safety check will flag this automatically) -- treat these
  as high-priority review items even if the technician believes the issue
  is resolved.

## Who to escalate to
- Single-asset hardware issues: on-site field lead.
- Multi-asset / site-wide issues: network or power infrastructure team,
  not individual field technicians.
- Inventory shortfalls that block an active repair: inventory manager
  (see the [inventory reorder policy](inventory-reorder-policy.md) for
  how re-orders are normally triggered automatically).

## SLA targets
- `critical` status: acknowledge within 15 minutes, on-site or remote
  mitigation within 2 hours.
- `degraded` status: acknowledge within 1 hour, resolution within 24
  hours.
