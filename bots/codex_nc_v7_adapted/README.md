# V7-based adaptation — next-round candidate, not proven champion

Adds exact heads-up river public-card outcome guards, conservative use of uniform-hidden-card equity, wider late opens and 2.25 BB late sizing, and restores the no-limper foldbot guard. SHA-256: 418902a7a99d1da027bcc541d01fc66424ef3e38c9dea11e753d452d8deddb35.

Fresh mixed test: 16.33 versus NC V7 14.01 over 192 tables, difference CI [-0.55, +5.19]. Balanced 18-policy league: fourth by point estimate, 16.95 versus V7 tenth at 14.77; rankings uncertain. Not a demonstrated top-three tournament bot. Passed tactical/public-river tests, static checker, and 32-table subprocess test with zero failed decisions. Never uploaded.

See arena/benchmarks/nc-v7-adaptation/README.md for the full history analysis, failed experiments, source hashes and limits.
