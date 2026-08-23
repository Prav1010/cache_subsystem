"""
Associativity trade-off sweep.

Holds total cache size fixed and sweeps associativity (1 = direct-mapped
through 16-way), measuring hit rate per trace using the golden model.
This is where the worst_case trace's design intent becomes visible: it's
constructed to conflict into a single set, so hit rate should improve
dramatically as associativity increases past the trace's conflict degree.

Writes results to analysis/results/associativity_trade_offs.csv and,
if matplotlib is available, a plot to
analysis/results/associativity_trade_offs.png.

Run from the analysis/ directory:
    python associativity_trade_offs.py
"""

import sys
import os
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tb"))
from cache_model_golden import GoldenCache

TRACE_DIR = os.path.join(os.path.dirname(__file__), "..", "tb", "test_patterns")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Fixed total cache size and line size for this sweep
CACHE_SIZE_BYTES = 4096
LINE_SIZE_BYTES  = 32
WRITE_BACK       = True

# Associativities to sweep - must each evenly divide
# (CACHE_SIZE_BYTES / LINE_SIZE_BYTES)
ASSOCIATIVITIES = [1, 2, 4, 8, 16]

TRACES = ["sequential_access", "random_access", "working_set", "worst_case"]


def load_trace(trace_name):
    accesses = []
    path = os.path.join(TRACE_DIR, f"{trace_name}.txt")
    with open(path) as f:
        for line in f:
            parts = line.split()
            addr = int(parts[0], 16)
            is_write = int(parts[1]) == 1
            accesses.append((addr, is_write))
    return accesses


def run_sweep():
    os.makedirs(RESULTS_DIR, exist_ok=True)

    trace_data = {name: load_trace(name) for name in TRACES}

    results = []  # list of (trace_name, associativity, hit_rate)

    for assoc in ASSOCIATIVITIES:
        num_lines = CACHE_SIZE_BYTES // LINE_SIZE_BYTES
        if num_lines % assoc != 0:
            print(f"Skipping associativity={assoc}: does not evenly divide num_lines={num_lines}")
            continue

        for trace_name, accesses in trace_data.items():
            cache = GoldenCache(CACHE_SIZE_BYTES, LINE_SIZE_BYTES, assoc, WRITE_BACK)
            for addr, is_write in accesses:
                cache.access(addr, is_write)
            results.append((trace_name, assoc, cache.hit_rate()))
            print(f"associativity={assoc:>2}-way trace={trace_name:<18} hit_rate={cache.hit_rate():.3f}")

    # Write CSV
    csv_path = os.path.join(RESULTS_DIR, "associativity_trade_offs.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trace", "associativity", "hit_rate"])
        writer.writerows(results)
    print(f"\nWrote {csv_path}")

    # Optional plot
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 5))
        for trace_name in TRACES:
            assocs = [r[1] for r in results if r[0] == trace_name]
            hit_rates = [r[2] for r in results if r[0] == trace_name]
            plt.plot(assocs, hit_rates, marker="o", label=trace_name)

        plt.xlabel("Associativity (ways)")
        plt.ylabel("Hit Rate")
        plt.title(f"Hit Rate vs. Associativity (cache size={CACHE_SIZE_BYTES}B, line={LINE_SIZE_BYTES}B)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        png_path = os.path.join(RESULTS_DIR, "associativity_trade_offs.png")
        plt.savefig(png_path, dpi=150)
        print(f"Wrote {png_path}")
    except ImportError:
        print("matplotlib not installed - skipping plot generation (CSV data is still complete)")


if __name__ == "__main__":
    run_sweep()