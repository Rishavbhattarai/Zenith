<!-- Demo knowledge-base content for the Zenith AI Support Agent (Phase 4.2). Not a real operations manual. -->

# Inventory Reorder Policy

## How autonomous re-ordering works
Every part in the catalog has a `stock_quantity`, a `reorder_threshold`,
and a `reorder_quantity`. Whenever a field technician logs a part
installation (via the field note app or directly), the inventory system:

1. Decrements `stock_quantity` by the quantity used.
2. Checks whether the new `stock_quantity` has dropped below
   `reorder_threshold`.
3. If so, and there isn't already a pending re-order for that part,
   automatically creates a re-order request for `reorder_quantity` units.

This means stock is checked and re-ordered in real time as parts are
consumed, rather than on a periodic inventory audit.

## Why a part might not trigger a re-order
- The part name in the field note didn't match the catalog exactly (the
  system reports these as "unmatched" rather than silently guessing).
- There's already a pending re-order for that part -- the system
  deliberately avoids stacking duplicate re-order requests for the same
  part.

## Adjusting thresholds
Reorder thresholds and quantities can only be changed by an inventory
administrator, not by field technicians -- this is enforced at the API
level, not just in the UI.
