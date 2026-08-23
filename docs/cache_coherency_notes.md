# Cache Coherency Notes

## 1. Scope of This Document

This project implements a **single cache** (one controller, one set of tag/data arrays) - there is no second cache, no shared memory system with multiple caching agents, and therefore no actual coherency protocol implemented in the RTL. This document exists to be explicit about that scope boundary and to discuss what would be needed if this design were extended into a multi-cache (e.g., multi-core) system, since coherency is a natural and important follow-up question for any cache design.

## 2. What "Coherency" Means

Cache coherency becomes a concern the moment more than one cache (or a cache plus a differently-cached view of the same memory) can hold a copy of the same memory location. The core problem: if core A writes to address X and it only updates core A's cache, core B's cache (if it also cached address X) now holds stale data - coherency protocols exist to detect and resolve this.

This single-cache design has no such problem *internally*, because there is exactly one cache and one "view" of memory-through-the-cache. The concern would only arise if this cache were instantiated multiple times (e.g., one per CPU core) sharing a common backing memory.

## 3. Write-Through vs. Write-Back and Coherency

This is relevant context because write policy interacts directly with how hard coherency would be to add later:

- **Write-through**: every write immediately (conceptually) propagates to memory. In a multi-cache system, this makes coherency easier to reason about, since memory is always up to date - other caches "merely" need to be notified/invalidated when a line they hold is written elsewhere (e.g., via a bus-snooping invalidate protocol).
- **Write-back** (the mode this design defaults to and primarily documents): writes stay local to the cache until eviction. This is more efficient (fewer memory writes) but makes coherency substantially harder in a multi-cache system, since memory can be stale for a long time relative to what's cached, and another cache reading that address from memory would get outdated data unless a coherency protocol intervened.

## 4. What a Real Multi-Cache Extension Would Need

If this single-cache design were extended to a shared-memory multi-core system, the standard next step would be a coherency protocol such as:

- **MSI** (Modified/Shared/Invalid): the simplest common protocol - each line is in one of three states, and bus transactions (or a directory) coordinate transitions between them across caches.
- **MESI** (adds Exclusive): distinguishes "I'm the only cache holding this line, and it's clean" from "shared" - lets a cache silently transition to Modified without a bus transaction if it already knows it's the exclusive holder, which MSI cannot do.
- **MOESI**: adds an Owned state, letting a modified line be shared directly between caches without first writing back to memory - relevant specifically in write-back systems like this one, where avoiding an unnecessary memory round-trip on cache-to-cache sharing is a meaningful performance win.

Implementing any of these would require: (1) a way for each cache to observe other caches' transactions (a shared bus with snooping, or a centralized directory), (2) additional per-line state bits beyond this design's valid/dirty (at minimum a full MSI/MESI/MOESI state encoding), and (3) a controller FSM extended to handle coherency-triggered transitions (e.g., invalidating a line because another cache just claimed exclusive ownership) in addition to the local hit/miss/replacement logic this project already implements.

## 5. Why This Wasn't Implemented

Adding real multi-cache coherency would roughly double the project's scope (a second cache instance, a shared memory/bus model, and a full coherency FSM) and shift the focus away from this project's core goal - demonstrating solid single-cache design, configurability, and verification rigor. It's documented here explicitly as the natural next step for anyone (including a future version of this project) wanting to extend this design toward a multi-core context, rather than left as an unstated gap.