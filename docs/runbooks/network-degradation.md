<!-- Demo knowledge-base content for the Zenith AI Support Agent (Phase 4.2). Not a real operations manual. -->

# Network Degradation

## Symptoms
Elevated `latency_ms`, rising `packet_loss_pct`, or a weakening
`signal_strength` reading (more negative dBm values) on an asset generally
indicates a network-layer problem rather than a compute or power issue.

## Diagnostic steps
1. Check whether `signal_strength` is degrading gradually (antenna/cabling
   wear, environmental interference) or dropped sharply at a single point
   in time (physical disconnection, hardware fault).
2. Compare `packet_loss_pct` against `latency_ms` -- high loss with normal
   latency suggests a flaky physical link; high latency with low loss
   suggests congestion or routing rather than a hardware fault.
3. Check whether neighboring assets in the same location are also
   affected. Multiple simultaneous degradations at one site point to
   shared infrastructure (switch, uplink) rather than a single node.

## Resolution
- For a single degraded node: reseat or replace the network card.
- For multiple nodes at one location: escalate to network infrastructure
  rather than dispatching a field tech per-asset.

## Escalation
Any location reporting more than 3 simultaneously degraded or critical
assets should be escalated immediately per the
[escalation policy](escalation-policy.md) rather than worked node-by-node.
