`timescale 1ns/1ps

// Configuration package for the cache subsystem
// All cache parameters are derived from three top-level choices:
// CACHE_SIZE_BYTES, LINE_SIZE_BYTES, ASSOCIATIVITY. Everything else
// (number of sets, index/offset/tag bit widths) is computed from these.
package cache_config_pkg;

    // ------------------------------------------------------------
    // Top-level configuration (override via parameter when instantiating)
    // ------------------------------------------------------------
    parameter int CACHE_SIZE_BYTES = 4096;    // 1KB to 256KB
    parameter int LINE_SIZE_BYTES  = 32;      // 16B to 128B
    parameter int ASSOCIATIVITY    = 4;       // 1 (direct-mapped) to 16-way
    parameter int ADDR_WIDTH       = 32;      // address bus width

    // Write policy: 0 = write-through, 1 = write-back
    parameter bit WRITE_BACK = 1'b1;

    // Miss penalty modeling: fixed number of cycles a miss takes to
    // resolve (models fetching a line from "main memory"), and separately
    // the number of extra cycles a write-back eviction costs on top of
    // that, if the evicted line was dirty (write-back mode only).
    parameter int MISS_PENALTY_CYCLES     = 20;
    parameter int WRITEBACK_PENALTY_CYCLES = 10;

    // ------------------------------------------------------------
    // Derived parameters
    // ------------------------------------------------------------
    parameter int NUM_LINES = CACHE_SIZE_BYTES / LINE_SIZE_BYTES;
    parameter int NUM_SETS  = NUM_LINES / ASSOCIATIVITY;

    parameter int OFFSET_BITS = $clog2(LINE_SIZE_BYTES);
    parameter int INDEX_BITS  = $clog2(NUM_SETS);
    parameter int TAG_BITS    = ADDR_WIDTH - INDEX_BITS - OFFSET_BITS;

    // Way-select width (enough bits to index which way within a set,
    // e.g. for 4-way associativity, WAY_BITS = 2)
    parameter int WAY_BITS = (ASSOCIATIVITY > 1) ? $clog2(ASSOCIATIVITY) : 1;

endpackage