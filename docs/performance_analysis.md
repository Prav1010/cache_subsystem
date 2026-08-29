# Performance Analysis

## 1. Overview

This document reports cache performance (hit rate, miss rate) across different configurations, using the Python golden model as the measurement engine (verified to match the RTL's hit/miss behavior exactly via `tb/cache_tb.sv` - see `sim/results/hit_miss_analysis.txt` for the 4/4 PASS confirmation across all traces).

## 2. Hit Rate vs. Cache Size

Sweep: associativity=4, line size=32B, sizes 1KB-256KB. Full data in `analysis/results/hit_rate_vs_size.csv`.

| Cache Size | sequential_access | random_access | working_set | worst_case |
|---|---|---|---|---|
| 1KB | 0.965 | 0.025 | 0.920 | 0.000 |
| 2KB | 0.965 | 0.040 | 0.920 | 0.000 |
| 4KB | 0.965 | 0.055 | 0.920 | 0.000 |
| 8KB | 0.965 | 0.070 | 0.920 | 0.975 |
| 16KB | 0.965 | 0.075 | 0.920 | 0.975 |
| 32KB-256KB | 0.965 | 0.075 | 0.920 | 0.975 |

**Findings:**
- `sequential_access` and `working_set` are completely flat across every size tested - both traces were designed around a small, fixed working set that fits even in the smallest (1KB) cache, so additional capacity provides no benefit.
- `random_access` improves only marginally (2.5% -> 7.5%) even at 256x the starting size, and plateaus by 8KB - consistent with its design intent: uniformly random addresses across a wide range have essentially no spatial or temporal locality for a larger cache to exploit.
- `worst_case` shows a sharp step: 0% hit rate at 1KB-4KB, jumping to 97.5% at 8KB and staying there. This is a clean, direct confirmation of the trace's design: `worst_case.txt` was constructed to conflict into a single set of a 4KB/4-way-associative cache (5 addresses cycling through one set, guaranteeing eviction-before-reuse). Once the cache is large enough (8KB+) that those same addresses now map across *multiple* sets instead of colliding into one, the artificial conflict disappears entirely and the trace becomes trivially cacheable.

## 3. Associativity Trade-offs

Sweep: cache size=4096B, line size=32B, associativity 1-16 way. Full data in `analysis/results/associativity_trade_offs.csv`.

| Associativity | sequential_access | random_access | working_set | worst_case |
|---|---|---|---|---|
| 1-way (direct-mapped) | 0.965 | 0.045 | 0.920 | 0.585 |
| 2-way | 0.965 | 0.050 | 0.920 | 0.390 |
| 4-way | 0.965 | 0.055 | 0.920 | 0.000 |
| 8-way | 0.965 | 0.055 | 0.920 | 0.975 |
| 16-way | 0.965 | 0.055 | 0.920 | 0.975 |

**Findings:**
- `sequential_access` and `working_set` are again flat - their working sets are small and evenly distributed enough that associativity doesn't change the outcome.
- `random_access` improves very slightly with associativity (4.5% -> 5.5%) and plateaus at 4-way - a small, expected effect since higher associativity reduces the chance that two randomly-colliding addresses evict each other prematurely, but random access has no strong locality for associativity to meaningfully exploit.
- `worst_case` shows a striking **non-monotonic** curve: 58.5% (1-way) -> 39.0% (2-way) -> **0.0% (4-way)** -> 97.5% (8-way) -> 97.5% (16-way). This is the standout result of this entire analysis and worth explaining directly: `worst_case.txt` was constructed with exactly `ASSOCIATIVITY + 1 = 5` addresses cycling through one set, using the *default* config's associativity (4) as the construction parameter. At 4-way, this produces the worst possible outcome by design - every single access misses, since the set can hold only 4 of the 5 constantly-recurring lines. At lower associativity (1-way, 2-way), the trace's conflict pattern doesn't align as destructively with the smaller set capacity in the same way, so some accesses get lucky partial reuse before the next conflicting address arrives - hence the *counter-intuitive* result that less associativity actually does slightly better than the exact thrash point. At 8-way and above, the set is now large enough to hold all 5 conflicting lines simultaneously, so nothing ever gets evicted after the initial warm-up - hit rate jumps to 97.5%.

## 4. The Central Takeaway

`worst_case.txt`'s hit rate is not a smooth curve in either sweep - it's a step function, precisely because it was engineered as an adversarial trace targeting one specific configuration (4KB / 4-way). This demonstrates a broader point: **cache performance depends on the interaction between workload structure and cache configuration**, not on cache size or associativity in isolation. A cache configuration that looks strictly "better" on paper (larger, more associative) doesn't uniformly outperform a smaller one for every workload - as the 1-way vs. 4-way comparison for `worst_case` shows, a smaller-associativity cache can occasionally outperform a mid-range one purely because a specific adversarial pattern happens to align worse with the mid-range configuration.

## 5. Writeback Frequency

From the earlier golden-model/RTL cross-check (see `sim/results/hit_miss_analysis.txt`), at the default configuration (4KB, 4-way, write-back):

| Trace | Writebacks | Notes |
|---|---|---|
| sequential_access | 0 | No writes ever evict a dirty line within this trace's length |
| random_access | 18 | The only trace in the base verification run with meaningful write+eviction interaction |
| working_set | 0 | Small working set never forces eviction of a dirty line |
| worst_case | 0 | All accesses are reads in this trace, so no dirty lines ever exist to write back |

## 6. Methodology Note

All hit-rate figures in this document come from the Python golden model (`tb/cache_model_golden.py`), independently verified against the RTL's actual hit/miss decisions via the trace-based testbench (`tb/cache_tb.sv` - see `sim/results/hit_miss_analysis.txt` for the 4/4 PASS confirmation, including exact writeback-count matching). Using the golden model for these broad configuration sweeps (14 total configurations across both sweeps) is valid and vastly faster than re-running full RTL simulation for every size/associativity combination.