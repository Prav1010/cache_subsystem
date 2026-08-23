"""
Hit rate vs. cache size sweep.

Uses the (already RTL-verified) Python golden model to measure hit rate
across a range of cache sizes, for each of the four workload traces.
Writes results to analysis/results/hit_rate_vs_size.csv and, if
matplotlib is available, a plot to analysis/results/hit_rate_vs_size.png.

Run from the analysis/ directory:
    python hit_rate_vs_size.py
"""

import sys
import os
import csv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "tb"))
from cache_model_golden import GoldenCache

TRACE_DIR = os.path.join(os.path.dirname(__file__), "..", "tb", "test_patterns")
RESULTS_DIR = os.path.join(os.path.dirname(__file__), "results")

# Fixed parameters for this sweep
LINE_SIZE_BYTES = 32
ASSOCIATIVITY   = 4
WRITE_BACK      = True

# Cache sizes to sweep (bytes) - must each be evenly divisible by
# LINE_SIZE_BYTES * ASSOCIATIVITY
CACHE_SIZES = [1024, 2048, 4096, 8192, 16384, 32768, 65536, 131072, 262144]

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

    results = []  # list of (trace_name, cache_size_bytes, hit_rate)

    for size in CACHE_SIZES:
        for trace_name, accesses in trace_data.items():
            cache = GoldenCache(size, LINE_SIZE_BYTES, ASSOCIATIVITY, WRITE_BACK)
            for addr, is_write in accesses:
                cache.access(addr, is_write)
            results.append((trace_name, size, cache.hit_rate()))
            print(f"size={size:>7}B trace={trace_name:<18} hit_rate={cache.hit_rate():.3f}")

    # Write CSV
    csv_path = os.path.join(RESULTS_DIR, "hit_rate_vs_size.csv")
    with open(csv_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["trace", "cache_size_bytes", "hit_rate"])
        writer.writerows(results)
    print(f"\nWrote {csv_path}")

    # Optional plot
    try:
        import matplotlib.pyplot as plt

        plt.figure(figsize=(8, 5))
        for trace_name in TRACES:
            sizes = [r[1] for r in results if r[0] == trace_name]
            hit_rates = [r[2] for r in results if r[0] == trace_name]
            plt.plot(sizes, hit_rates, marker="o", label=trace_name)

        plt.xscale("log", base=2)
        plt.xlabel("Cache Size (Bytes)")
        plt.ylabel("Hit Rate")
        plt.title(f"Hit Rate vs. Cache Size (associativity={ASSOCIATIVITY}, line={LINE_SIZE_BYTES}B)")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        png_path = os.path.join(RESULTS_DIR, "hit_rate_vs_size.png")
        plt.savefig(png_path, dpi=150)
        print(f"Wrote {png_path}")
    except ImportError:
        print("matplotlib not installed - skipping plot generation (CSV data is still complete)")


if __name__ == "__main__":
    run_sweep()