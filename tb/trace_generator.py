"""
Trace generator for cache subsystem verification.

Generates four kinds of memory access traces, each targeting a
different aspect of cache behavior:

  sequential_access.txt - strictly increasing addresses (best case for
                           spatial locality; should show a high hit rate
                           once lines are warmed up, since each line
                           serves multiple sequential accesses)

  random_access.txt     - uniformly random addresses across a wide range
                           (worst case for locality; expected to show a
                           much lower hit rate than sequential)

  working_set.txt        - repeatedly cycles through a small, fixed set
                            of addresses (models a realistic "hot" working
                            set that fits or nearly fits in the cache;
                            should show a high hit rate after warm-up,
                            and is useful for observing associativity
                            effects - e.g. a working set slightly larger
                            than a direct-mapped cache's set count will
                            cause thrashing that higher associativity avoids)

  worst_case.txt          - deliberately constructed to thrash a specific
                             associativity: cycles through (associativity + 1)
                             addresses that all map to the SAME set, which
                             guarantees a miss on every single access
                             regardless of LRU policy, since the working
                             set for that one set exceeds the set's capacity

Each trace file line format: "addr is_write [write_byte]"
  addr:       hex address (e.g. 0x1000)
  is_write:   0 = read, 1 = write
  write_byte: hex byte value (only present if is_write == 1)

Run this to (re)generate all four trace files:
    python trace_generator.py
"""

import random

OUTPUT_DIR = "test_patterns"
RANDOM_SEED = 7

# These should match the cache configuration under test (see
# cache_config_pkg.sv defaults) so worst_case.txt can be constructed to
# deliberately alias into the same set.
LINE_SIZE_BYTES = 32
NUM_SETS        = 32   # matches CACHE_SIZE_BYTES=4096, ASSOCIATIVITY=4 default config
ASSOCIATIVITY   = 4


def write_trace(filename, accesses):
    with open(f"{OUTPUT_DIR}/{filename}", "w") as f:
        for addr, is_write, *rest in accesses:
            if is_write:
                write_byte = rest[0] if rest else 0xAA
                f.write(f"{addr:#010x} 1 {write_byte:#04x}\n")
            else:
                f.write(f"{addr:#010x} 0\n")
    print(f"Wrote {len(accesses)} accesses to {OUTPUT_DIR}/{filename}")


def gen_sequential(num_accesses=200):
    """Strictly increasing byte addresses, one byte per access."""
    accesses = []
    for i in range(num_accesses):
        addr = i  # sequential byte addresses
        is_write = (i % 5 == 0)  # occasional writes mixed in
        accesses.append((addr, is_write))
    return accesses


def gen_random(num_accesses=200, addr_range=0x10000):
    """Uniformly random addresses across a wide range - poor locality."""
    rng = random.Random(RANDOM_SEED)
    accesses = []
    for _ in range(num_accesses):
        addr = rng.randint(0, addr_range - 1)
        is_write = rng.random() < 0.2
        accesses.append((addr, is_write))
    return accesses


def gen_working_set(num_accesses=200, working_set_size=16):
    """Repeatedly cycle through a small, fixed set of addresses."""
    rng = random.Random(RANDOM_SEED + 1)
    # Working set addresses spread across a few different lines
    working_addrs = [i * LINE_SIZE_BYTES for i in range(working_set_size)]
    accesses = []
    for _ in range(num_accesses):
        addr = rng.choice(working_addrs)
        is_write = rng.random() < 0.15
        accesses.append((addr, is_write))
    return accesses


def gen_worst_case(num_accesses=200):
    """
    Cycle through (ASSOCIATIVITY + 1) addresses that all map to set 0,
    guaranteeing a miss on every access once the cycle length exceeds
    what the set can hold, regardless of replacement policy.
    Addresses are constructed as: tag * (NUM_SETS * LINE_SIZE_BYTES) + 0,
    which all decode to index=0 but with different tags.
    """
    stride = NUM_SETS * LINE_SIZE_BYTES
    conflicting_addrs = [tag * stride for tag in range(ASSOCIATIVITY + 1)]
    accesses = []
    for i in range(num_accesses):
        addr = conflicting_addrs[i % len(conflicting_addrs)]
        accesses.append((addr, False))
    return accesses


def main():
    write_trace("sequential_access.txt", gen_sequential())
    write_trace("random_access.txt", gen_random())
    write_trace("working_set.txt", gen_working_set())
    write_trace("worst_case.txt", gen_worst_case())


if __name__ == "__main__":
    main()