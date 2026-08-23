# Performance Analysis

**Status: sections marked TBD will be filled in after running `analysis/hit_rate_vs_size.py` and `analysis/associativity_trade_offs.py`.**

## 1. Overview

This document reports cache performance (hit rate, miss rate) across different configurations, using the Python golden model as the measurement engine (since sweeping many configurations through full RTL simulation would be slow; the golden model has already been verified to match the RTL's hit/miss behavior exactly via `tb/cache_tb.sv`, so it's a valid stand-in for these sweep studies).

## 2. Hit Rate vs. Cache Size

TBD - see `analysis/results/` for generated data and `analysis/hit_rate_vs_size.py` for the sweep script. Expected trend: hit rate should generally increase with cache size (more lines available to hold the working set) with diminishing returns once the cache is large enough to hold the full working set of a given trace.

## 3. Associativity Trade-offs

TBD - see `analysis/results/` and `analysis/associativity_trade_offs.py`. Expected trend: higher associativity should improve hit rate particularly for traces with set-conflict-heavy access patterns (see `worst_case.txt`, which is specifically constructed to thrash low-associativity configurations), with the improvement shrinking as associativity approaches the point where the whole cache is effectively fully associative for the given trace's working set.

## 4. Per-Trace Results Summary

| Trace | Description | Hit Rate (default config) | Notes |
|-------|--------------|------------------------------|-------|
| sequential_access | Strictly increasing addresses | TBD | Expected high (spatial locality within each line) |
| random_access | Uniformly random addresses | TBD | Expected low (no locality) |
| working_set | Repeated access to a small fixed address set | TBD | Expected high once warmed up |
| worst_case | Addresses deliberately conflicting into one set | TBD | Expected very low - constructed specifically to thrash the default 4-way associativity |

Default config for this table: CACHE_SIZE_BYTES=4096, LINE_SIZE_BYTES=32, ASSOCIATIVITY=4, WRITE_BACK=1 (see `rtl/cache_config_pkg.sv`).

## 5. Writeback Frequency (Write-Back Mode)

TBD - reports how often evictions require a write-back (i.e., how often the evicted line was dirty) per trace, which directly affects the average miss penalty in write-back mode (`MISS_PENALTY_CYCLES` alone vs. `MISS_PENALTY_CYCLES + WRITEBACK_PENALTY_CYCLES`).

## 6. Methodology Note

All hit-rate figures in this document come from the Python golden model (`tb/cache_model_golden.py`), not from timing a real RTL simulation run per configuration. This is a deliberate methodology choice: the golden model was independently verified against the RTL's actual hit/miss decisions via the trace-based testbench (`tb/cache_tb.sv`, see `sim/results/hit_miss_analysis.txt` for the pass/fail confirmation), so using it for broad configuration sweeps is valid and vastly faster than re-running full RTL simulation for every size/associativity combination.