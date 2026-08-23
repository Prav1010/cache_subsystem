# Design Choices and Rationale

A consolidated summary of the key architectural decisions in this project and why each was made - pulling together reasoning that's also detailed in the more specific docs (`lru_replacement_algorithm.md`, `cache_coherency_notes.md`, `cache_specification.md`).

## 1. Why LRU (Not FIFO, Random, or Pseudo-LRU)?

See `docs/lru_replacement_algorithm.md` for the full comparison. Short version: exact LRU gives the best hit rate of the options considered, and its precise definition makes it straightforward to implement identically in RTL and in the Python golden model - directly supporting this project's verification-rigor goal. The cost (age-counter state scaling with associativity) is real but bounded and quantified in the synthesis area report.

## 2. Why Model Miss Penalty as a Fixed Cycle Count Instead of a Real Memory Interface?

A real memory interface (with its own protocol, variable latency, possibly a bus arbiter) would add substantial scope without changing what this project is actually trying to demonstrate: correct cache control logic, replacement policy behavior, and write-policy handling. A fixed, configurable `MISS_PENALTY_CYCLES` (and separately `WRITEBACK_PENALTY_CYCLES`) captures the *timing effect* of a miss - the controller genuinely stalls for that many cycles, and this is directly observable and verifiable in simulation - without requiring a full memory subsystem to be designed and verified alongside the cache itself.

## 3. Why Simplify Writes to One Byte at a Time?

Real caches typically support word-or-wider writes, sub-word write masking, etc. This design's `req_wdata` is a single byte per write request, written to a specific `byte_offset` within a line. This keeps the data array's write port simple (`byte_write_en` + `byte_offset` + one byte of data) while still fully exercising the write-hit, dirty-bit, and write-back logic that's actually the point of this project. Extending to wider writes with byte-enable masking would be a straightforward RTL extension, not a redesign - the FSM and write-policy logic wouldn't fundamentally change.

## 4. Why No Real Coherency Protocol?

See `docs/cache_coherency_notes.md` for the full discussion. Short version: this is a single-cache design; coherency only becomes a real concern with multiple caches sharing memory (e.g., multi-core), which is out of scope here but explicitly documented as the natural next step.

## 5. Why Two Separate Tag and Data Arrays (Not a Combined Structure)?

Splitting `cache_tagarray` and `cache_dataarray` into separate modules mirrors how real cache hardware is typically organized (tag comparison can happen in parallel with, and independently of, data access) and makes each piece easier to verify in isolation - the tag array's hit/miss/eviction-query logic can be reasoned about without needing to think about the (much wider) data storage at the same time.

## 6. Why a Separate cache_lru Module (Not Folded Into the Controller)?

Keeping LRU tracking as its own module with a clean `access_valid/access_set/access_way` in, `victim_way` out interface means the replacement policy could be swapped out (e.g., for a pseudo-LRU or random-replacement module with the same interface) without touching the controller's FSM logic - the controller doesn't need to know *how* the victim way is chosen, only that it can ask for one.

## 7. Why Exact LRU's Hardware Cost Wasn't a Blocker Here

This is a portfolio/learning project, not an area-constrained production design - the goal is to demonstrate the trade-off is understood (see Section 1 and `docs/lru_replacement_algorithm.md`), not to pick the objectively "correct" answer for every real-world context. The synthesis area report (`docs/synthesis_results.md`, once populated) provides the real data to have an informed conversation about when this trade-off would tip the other way (e.g., at high associativity in an area-constrained embedded design).