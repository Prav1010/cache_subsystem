# Cache Subsystem Specification

## 1. Overview

This document specifies a configurable set-associative cache subsystem: configurable size, associativity, line size, LRU replacement, and write-through or write-back write policy, with modeled (not real) miss penalty timing.

## 2. Configuration Parameters

| Parameter | Range | Description |
|-----------|-------|--------------|
| CACHE_SIZE_BYTES | 1KB - 256KB | Total cache capacity |
| LINE_SIZE_BYTES | 16B - 128B | Bytes per cache line |
| ASSOCIATIVITY | 1 (direct-mapped) - 16-way | Number of ways per set |
| WRITE_BACK | 0 or 1 | 0 = write-through, 1 = write-back |
| MISS_PENALTY_CYCLES | designer choice | Cycles a miss takes to resolve (models memory fetch latency) |
| WRITEBACK_PENALTY_CYCLES | designer choice | Additional cycles for a dirty eviction's write-back (write-back mode only) |

Derived: `NUM_SETS = (CACHE_SIZE_BYTES / LINE_SIZE_BYTES) / ASSOCIATIVITY`, with address split into `[TAG | INDEX | OFFSET]` fields sized from `OFFSET_BITS = log2(LINE_SIZE_BYTES)`, `INDEX_BITS = log2(NUM_SETS)`, `TAG_BITS = ADDR_WIDTH - INDEX_BITS - OFFSET_BITS`.

## 3. Module Hierarchy
cache_controller (top-level FSM: hit/miss detection, fill sequencing, write policy logic)
├── cache_tagarray (tag/valid/dirty storage, parallel hit detection across all ways)
├── cache_dataarray (line data storage, one array indexed by set+way)
└── cache_lru (exact LRU age-counter tracking per set)


## 4. Request/Response Interface

| Signal | Direction | Description |
|--------|-----------|--------------|
| req_valid | input | Request is being issued this cycle |
| req_is_write | input | 1 = write, 0 = read |
| req_addr | input | Full address |
| req_wdata | input | Byte to write (simplified: one byte per write request) |
| resp_valid | output | Response is ready this cycle |
| resp_hit | output | 1 = the completed access was a hit (0 if it required a miss resolution) |
| resp_rdata | output | Read data byte (valid on a read response) |
| busy | output | 1 = a miss is being serviced; new requests should wait |

## 5. Hit Path

On a hit: the tag array reports `hit=1` and the hitting way; the response is returned the **same cycle**. A read returns the addressed byte from that way's line; a write updates the byte in the data array and (in write-back mode) marks the line dirty. The LRU tracker is updated to mark the hitting way as most-recently-used.

## 6. Miss Path

On a miss (`FSM: S_IDLE -> S_MISS_WAIT -> [S_WRITEBACK_WAIT] -> S_FILL -> S_IDLE`):
1. The original request is latched (address, read/write, write data).
2. `S_MISS_WAIT` holds for `MISS_PENALTY_CYCLES`, modeling the latency of fetching the requested line from main memory.
3. The victim way (from LRU) is checked: if it's valid and dirty **and** the cache is in write-back mode, an additional `S_WRITEBACK_WAIT` of `WRITEBACK_PENALTY_CYCLES` models writing the evicted dirty line back to memory.
4. `S_FILL` installs the new line into the tag and data arrays (replacing the victim way), updates LRU, and returns the response.

**Important scope note**: this design does not model an actual backing memory - fetched line data is modeled as zero-filled content, since the focus of this project is cache *control logic and timing*, not full memory-system integration. This is documented explicitly here so it's clear this is a deliberate scope decision, not an oversight.

## 7. Write Policy

- **Write-through** (`WRITE_BACK=0`): a write hit updates the cache line's data; in a complete system it would also immediately push the write to main memory, but that memory-side push is not modeled in this project (see `docs/cache_coherency_notes.md`). No dirty bit tracking occurs in this mode.
- **Write-back** (`WRITE_BACK=1`): a write hit updates the cache line's data and sets the dirty bit; the write only reaches "memory" when the line is eventually evicted (modeled via the `S_WRITEBACK_WAIT` state and `stat_writeback_pulse`).

## 8. Replacement Policy

Exact LRU via per-way age counters (see `docs/lru_replacement_algorithm.md` for the full algorithm description and the comparative discussion of LRU vs. other policies).

## 9. Statistics

The controller emits three single-cycle event pulses (`stat_hit_pulse`, `stat_miss_pulse`, `stat_writeback_pulse`) that the testbench (or any surrounding system) accumulates into hit/miss/writeback counters - this keeps statistics collection outside the controller's own state, since counter width requirements vary by use case (a long-running simulation needs wider counters than the controller itself should need to carry).

## 10. Verification Strategy

An independent Python golden model (`tb/cache_model_golden.py`) reimplements the cache's set-associative lookup, exact LRU, and write policy behavior directly from this specification. `tb/trace_generator.py` produces four workload traces (sequential, random, working-set, worst-case) that are run through both the golden model (producing expected hit/miss/writeback counts) and the RTL testbench (`tb/cache_tb.sv`), with the RTL's observed statistics checked against the golden model's independently-computed expected statistics.