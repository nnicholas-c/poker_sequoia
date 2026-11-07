# Minimal river guard on the V4/V6 merge

Adds only guaranteed heads-up river outcomes to the older merged baseline: fold when no possible opponent hidden card can lose or tie, and continue when none can beat us. No new opening widths or random-range equity blend. SHA-256: df6580d139d44d292bbf1a90766dcde1be3d8aabee75ec3cdc1b8253dd66ea29.

Fresh mixed test versus NC V7: 16.46 versus 14.87 over 192 tables, difference CI [-1.22, +4.40]. Direct against its parent: 12.08 versus 12.92 over 96 tables, inconclusive. It was not included in the earlier balanced league. Passed tactical/public-river tests, static checker, and 16-table subprocess test with zero failed decisions. Never uploaded.
