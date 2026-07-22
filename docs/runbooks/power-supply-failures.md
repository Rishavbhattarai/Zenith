<!-- Demo knowledge-base content for the Zenith AI Support Agent (Phase 4.2). Not a real operations manual. -->

# Power Supply Failures

## Symptoms
A node reporting `power_draw` readings well above its normal baseline, or
telemetry status flipping between `nominal` and `critical` on the
`power_draw` metric, usually indicates a failing power supply unit (PSU).
Sudden drops to near-zero power draw combined with the node going
unresponsive on other metrics is also a strong signal.

## Diagnostic steps
1. Pull the last 20 telemetry readings for the affected asset and check
   whether `power_draw` is trending upward over time (gradual PSU
   degradation) or spiking erratically (failing capacitor).
2. Cross-check `cpu_temp` on the same asset -- PSU failures often cause
   secondary thermal issues as voltage regulation degrades.
3. If the asset has had a PSU replaced in the last 30 days, check whether
   this is a repeat failure (may indicate an installation defect rather
   than a worn part).

## Replacement procedure
1. Confirm the asset is drained of active workload before physical access.
2. Replace the power supply unit; log the replacement via the field note
   app so the part is recorded against inventory.
3. After replacement, monitor `power_draw` for 15 minutes to confirm it
   settles into the normal band before closing out the ticket.

## Escalation
If a third PSU failure occurs on the same asset within 90 days, escalate
per the [escalation policy](escalation-policy.md) -- this pattern usually
means the underlying issue isn't the PSU itself.
