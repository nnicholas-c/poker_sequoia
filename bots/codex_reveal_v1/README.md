# Codex reveal v1 — experimental baseline

Frozen source from the announced build window. SHA-256 of `agent.py`:
`c1152f3ce2ab5da640f5bdff0c578600b5bb2ebe39406329f4b223e9c45cea10`.

The generated three-card lookup table is required: package the folder, not `agent.py` alone. Generation used flop-only retention decisions, 1,755 suit-equivalent classes and 384 sampled deals per class; these are model estimates, not equilibrium values.

This version passed real process health checks but is **not recommended for promotion**. Four-versus-four tests in the official engine scored 13.1525 against 11.8475 for the original Claude snapshot, which later proved to have a silent flop/turn error. Against Claude v1 with that runtime error and its position calculation repaired, it lost 9.0 to 16.0 over 1,000 fresh tables (seed `practice1-codex-vs-repaired-1`, paired difference −7.0, approximate 95% interval [−7.783, −6.217]).

It remains in the shared pool as a reproducible internal opponent. Create a new version folder for improvements; do not relabel these results as results for changed code.
