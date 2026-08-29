# Configurable Cache Subsystem

A configurable set-associative cache implemented in Verilog/SystemVerilog: configurable size (1KB-256KB), associativity (direct-mapped to 16-way), line size (16B-128B), exact LRU replacement, and write-through or write-back write policy, with modeled miss-penalty timing. Verified against an independent Python golden model using realistic trace-based workloads, with full synthesis area/power/timing analysis.

## Features

- Fully configurable size, associativity, and line size via `cache_config_pkg.sv`
- Exact LRU replacement policy (age-counter based), generic across any associativity
- Write-through or write-back write policy (compile-time selectable)
- Modeled miss penalty and write-back penalty timing
- Independent Python golden model for verification (set-associative lookup, exact LRU, write policy - not derived from the RTL)
- Realistic trace-based workload generation: sequential, random, working-set, and worst-case (deliberately conflict-inducing) access patterns
- Performance analysis: hit rate vs. cache size, associativity trade-offs
- Full synthesis flow with timing/area/power reporting

## Module Hierarchy

cache_controller (top-level FSM)
├── cache_tagarray (tag/valid/dirty storage, hit detection)
├── cache_dataarray (line data storage)
└── cache_lru (exact LRU replacement tracking)


See `docs/cache_specification.md` for the full interface and behavior spec, `docs/lru_replacement_algorithm.md` for the replacement policy comparison, `docs/cache_coherency_notes.md` for scope boundaries around multi-cache coherency, and `docs/design_choices.md` for a consolidated rationale summary.

## Verification: Trace-Based, Golden-Model-Checked

`tb/cache_model_golden.py` is an independent Python cache simulator, written from the specification rather than the RTL. `tb/trace_generator.py` produces four distinct workload traces designed to exercise different behaviors:

| Trace | Purpose |
|-------|---------|
| sequential_access | Best-case spatial locality |
| random_access | Worst-case locality (no pattern) |
| working_set | Realistic repeated-access "hot" address set |
| worst_case | Deliberately conflicts into one set, thrashing low associativity |

Each trace is run through both the golden model and the RTL testbench (`tb/cache_tb.sv`); the RTL's observed hit/miss/writeback statistics are checked against the golden model's independently-computed expected statistics.

## How to Run

```bash
cd sim
./run_full_sim.sh
```

This script:
1. Generates all four trace files (`python trace_generator.py`)
2. Computes golden-model expected statistics for each trace
3. Compiles the RTL and testbench with Xilinx Vivado's simulator
4. Runs the RTL simulation against each trace and compares results
5. Writes a combined summary to `sim/results/hit_miss_analysis.txt`

## Performance Analysis

```bash
cd analysis
python hit_rate_vs_size.py
python associativity_trade_offs.py
```

Generates hit-rate-vs-configuration CSV data into `analysis/results/`. Full write-up with data tables in `docs/performance_analysis.md`.

**Headline finding**: `worst_case.txt` (constructed to conflict into a single set) produces a striking non-monotonic hit rate across associativity - 58.5% (1-way) -> 39.0% (2-way) -> **0.0% (4-way, exact thrash point)** -> 97.5% (8-way and above) - a clean demonstration that cache performance depends on the interaction between workload and configuration, not configuration size alone. See `docs/performance_analysis.md` Section 3-4 for the full explanation.

## Synthesis

```bash
cd synth
vivado -mode batch -source cache_synth.tcl
```

Produces timing, area, and power reports in `synth/reports/`.

## Repository Structure

cache_subsystem/
├── rtl/
│ ├── cache_controller.v # Top-level FSM
│ ├── cache_tagarray.v # Tag/valid/dirty storage, hit detection
│ ├── cache_dataarray.v # Line data storage
│ ├── cache_lru.v # Exact LRU replacement
│ ├── cache_config_pkg.sv # Configuration parameters
│ └── cache_interface.sv # Request/response type definitions
├── tb/
│ ├── cache_tb.sv # Main testbench
│ ├── cache_model_golden.py # Independent Python reference model
│ ├── trace_generator.py # Workload trace generator
│ └── test_patterns/ # Generated trace files
├── sim/
│ ├── run_full_sim.sh
│ ├── results/
│ └── analysis/
├── synth/
│ ├── cache_synth.tcl
│ ├── reports/
│ └── gates/
├── docs/
│ ├── cache_specification.md
│ ├── lru_replacement_algorithm.md
│ ├── cache_coherency_notes.md
│ ├── performance_analysis.md
│ └── design_choices.md
├── analysis/
│ ├── hit_rate_vs_size.py
│ ├── associativity_trade_offs.py
│ └── results/
├── presentation/
│ └── cache_design_overview.pptx
└── README.md