# LRU Replacement Algorithm

## 1. Why a Replacement Policy Is Needed

Once a set is full (all `ASSOCIATIVITY` ways hold valid lines), a miss requires evicting one existing line to make room for the new one. The replacement policy decides which line to evict. This only matters for associativity > 1 - a direct-mapped cache (associativity = 1) has no choice to make, since each address maps to exactly one possible line.

## 2. LRU (Least Recently Used) - Chosen Policy

**Intuition**: evict the line that hasn't been accessed for the longest time, on the assumption that lines used recently are more likely to be used again soon (temporal locality) than lines that haven't been touched in a while.

**Implementation (exact LRU via age counters)**: each way in a set has an age counter. On every access to that set:
- The accessed (or newly filled) way's counter resets to 0 (most-recently-used).
- Every other way's counter in that set increments by 1.

The victim on a future miss is whichever way currently has the **highest** age counter value in that set - the least recently used.

This is implemented in `rtl/cache_lru.v` and mirrored exactly in `tb/cache_model_golden.py`'s `_touch_lru`/`_find_victim` methods.

## 3. Alternatives Considered

### FIFO (First-In-First-Out)
Evict whichever line was installed longest ago, regardless of how recently it's been *accessed* since installation.
- **Simpler hardware**: just a single counter/pointer per set, no per-access updates needed on hits.
- **Worse hit rate in practice**: doesn't account for actual usage pattern - a line that was installed long ago but is still being accessed frequently gets evicted just as readily as one that's genuinely gone cold.

### Random Replacement
Pick a victim way uniformly at random.
- **Simplest hardware**: no state at all beyond a random number source.
- **Surprisingly competitive** in some workloads and used in real high-associativity designs (e.g., some ARM cache implementations) specifically because true LRU tracking becomes expensive at high associativity - but generally underperforms LRU for workloads with strong temporal locality.

### Pseudo-LRU (Tree-based approximation)
Rather than tracking exact recency with a full counter per way, uses a binary tree of single bits that approximately (not exactly) tracks which "half" of the ways was used more recently, recursively. Common in real CPU caches at higher associativity.
- **Much cheaper hardware**: O(ASSOCIATIVITY) bits total instead of O(ASSOCIATIVITY x log(ASSOCIATIVITY)) bits for exact age counters.
- **Approximation cost**: doesn't always evict the true least-recently-used way, just a reasonable approximation - the hit rate difference versus exact LRU is typically small in practice but not zero.

## 4. Why Exact LRU Was Chosen for This Project

1. **Verifiability**: exact LRU has a precise, unambiguous definition, making it straightforward to implement identically in both the RTL (`cache_lru.v`) and the Python golden model (`cache_model_golden.py`) and confirm they produce bit-for-bit identical eviction decisions - this directly supports the project's verification-rigor goal. A pseudo-LRU approximation's exact eviction behavior is more fiddly to specify and would make golden-model cross-checking less clean.
2. **Educational clarity**: the age-counter mechanism is easy to explain and reason about, which matters for a portfolio project meant to demonstrate understanding, not just working silicon.
3. **Acceptable cost at this scale**: this project's associativity range (up to 16-way) means the age-counter overhead (`AGE_BITS x ASSOCIATIVITY` bits per set) is a real but bounded cost - `docs/performance_analysis.md` and the synthesis area report quantify what this actually costs in practice as associativity increases.

## 5. Trade-off Summary

| Policy | Hardware Cost | Hit Rate (typical) | Verification Complexity |
|--------|-----------------|----------------------|---------------------------|
| Random | Lowest | Lowest | Low (no golden-model state to match) |
| FIFO | Low | Low-Moderate | Low |
| Pseudo-LRU | Moderate | Close to exact LRU | Moderate (approximation must be matched exactly between RTL and any model) |
| Exact LRU (chosen) | Highest (scales with associativity) | Best (of these options) | High but very well-defined |

If this design were being extended toward a very high-associativity (e.g., 16-way and beyond) production cache where area was tightly constrained, pseudo-LRU would be the natural next iteration - flagged here as a deliberate scope choice, consistent with the same reasoning applied to the ripple-carry adder decision in the `configurable_alu` project.