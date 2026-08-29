#!/bin/bash
# Full simulation flow for the cache subsystem:
# 1. Generate trace files (Python)
# 2. Run each trace through the Python golden model, save its stats
# 3. Compile the RTL once
# 4. Run the RTL simulation against each trace, compare vs golden stats
# 5. Collect results into sim/results/hit_miss_analysis.txt

set -e

echo "=== Step 1: Generating trace files ==="
cd ../tb
python trace_generator.py
cd ../sim

mkdir -p results
mkdir -p results/waveforms

TRACES=("sequential_access" "random_access" "working_set" "worst_case")

echo "=== Step 2: Computing golden model stats for each trace ==="
cd ../tb
python - <<'PYEOF'
import sys
sys.path.insert(0, ".")
from cache_model_golden import GoldenCache

# Must match cache_config_pkg.sv defaults
CACHE_SIZE_BYTES = 4096
LINE_SIZE_BYTES  = 32
ASSOCIATIVITY    = 4
WRITE_BACK       = True

traces = ["sequential_access", "random_access", "working_set", "worst_case"]

for trace_name in traces:
    cache = GoldenCache(CACHE_SIZE_BYTES, LINE_SIZE_BYTES, ASSOCIATIVITY, WRITE_BACK)
    with open(f"test_patterns/{trace_name}.txt") as f:
        for line in f:
            parts = line.split()
            addr = int(parts[0], 16)
            is_write = int(parts[1]) == 1
            cache.access(addr, is_write)

    with open(f"test_patterns/{trace_name}_golden_stats.txt", "w") as out:
        out.write(f"{cache.stats['accesses']} {cache.stats['hits']} "
                   f"{cache.stats['misses']} {cache.stats['writebacks']}\n")

    print(f"{trace_name}: accesses={cache.stats['accesses']} "
          f"hits={cache.stats['hits']} misses={cache.stats['misses']} "
          f"hit_rate={cache.hit_rate():.3f} writebacks={cache.stats['writebacks']}")
PYEOF
cd ../sim

echo "=== Step 3/4: Compiling and running RTL for each trace ==="
echo "trace,accesses,hits,misses,writebacks,hit_rate,result" > results/cache_stats.csv
> results/hit_miss_analysis.txt

for trace in "${TRACES[@]}"; do
    echo "--- Trace: $trace ---"

    cat > ../tb/trace_select.svh <<EOF
parameter TRACE_FILE  = "../../tb/test_patterns/${trace}.txt";
parameter GOLDEN_FILE = "../../tb/test_patterns/${trace}_golden_stats.txt";
EOF

    cd results
    xvlog --sv ../../rtl/cache_config_pkg.sv
    xvlog --sv ../../rtl/cache_interface.sv
    xvlog --sv ../../rtl/cache_lru.v
    xvlog --sv ../../rtl/cache_tagarray.v
    xvlog --sv ../../rtl/cache_dataarray.v
    xvlog --sv ../../rtl/cache_controller.v
    xvlog --sv -i ../../tb ../../tb/cache_tb.sv
    xelab cache_tb -s cache_tb_sim > "${trace}_elab_log.txt" 2>&1
    xsim cache_tb_sim -runall > "${trace}_sim_log.txt" 2>&1
    cd ..

    cat "results/${trace}_sim_log.txt" >> results/hit_miss_analysis.txt
    echo "" >> results/hit_miss_analysis.txt

    grep "RTL STATS\|RESULT" "results/${trace}_sim_log.txt"
done

echo "=== Simulation complete ==="
echo "Per-trace logs and combined analysis in sim/results/"

echo "=== Simulation complete ==="
echo "Per-trace logs and combined analysis in sim/results/"