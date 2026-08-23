"""
Golden model for the configurable cache subsystem.

This is an independent, pure-Python reference implementation of the
cache's behavior (set-associative lookup, exact LRU replacement,
write-through/write-back policy). It is written directly from
docs/cache_specification.md, NOT derived from or by inspecting the RTL,
so it serves as a genuine independent check.

Used to verify hit/miss decisions and to compute performance statistics
(hit rate, miss rate, writeback count) for a given access trace, which
can then be compared against the RTL simulation's reported stats and
against the same trace fed to the actual hardware testbench.
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class CacheLine:
    valid: bool = False
    dirty: bool = False
    tag: Optional[int] = None
    data: bytearray = field(default_factory=lambda: bytearray(1))  # placeholder; not used for hit/miss logic


class GoldenCache:
    def __init__(self, cache_size_bytes: int, line_size_bytes: int,
                 associativity: int, write_back: bool = True,
                 addr_width: int = 32):
        assert cache_size_bytes % (line_size_bytes * associativity) == 0, \
            "cache_size_bytes must be evenly divisible by line_size_bytes * associativity"

        self.cache_size_bytes = cache_size_bytes
        self.line_size_bytes = line_size_bytes
        self.associativity = associativity
        self.write_back = write_back
        self.addr_width = addr_width

        self.num_lines = cache_size_bytes // line_size_bytes
        self.num_sets = self.num_lines // associativity

        self.offset_bits = (line_size_bytes - 1).bit_length()
        self.index_bits = (self.num_sets - 1).bit_length() if self.num_sets > 1 else 0
        self.tag_bits = addr_width - self.index_bits - self.offset_bits

        # sets[set_idx] = list of CacheLine, one per way
        self.sets = [[CacheLine() for _ in range(associativity)] for _ in range(self.num_sets)]

        # LRU age tracking: age[set_idx][way] - lower = more recently used
        self.age = [[w for w in range(associativity)] for _ in range(self.num_sets)]

        # Statistics
        self.stats = {
            "accesses": 0,
            "hits": 0,
            "misses": 0,
            "reads": 0,
            "writes": 0,
            "writebacks": 0,
        }

    def _decode(self, addr: int):
        offset = addr & ((1 << self.offset_bits) - 1)
        index = (addr >> self.offset_bits) & ((1 << self.index_bits) - 1) if self.index_bits > 0 else 0
        tag = addr >> (self.offset_bits + self.index_bits)
        return tag, index, offset

    def _touch_lru(self, set_idx: int, way: int):
        """Mark `way` as most-recently-used in `set_idx`, aging all others."""
        for w in range(self.associativity):
            if w == way:
                self.age[set_idx][w] = 0
            else:
                self.age[set_idx][w] += 1

    def _find_victim(self, set_idx: int) -> int:
        """Return the way index with the highest age (least recently used)."""
        ages = self.age[set_idx]
        return max(range(self.associativity), key=lambda w: ages[w])

    def access(self, addr: int, is_write: bool) -> dict:
        """
        Perform one memory access. Returns a dict describing what happened:
        {hit: bool, way: int, evicted: bool, evicted_dirty: bool, writeback: bool}
        """
        self.stats["accesses"] += 1
        if is_write:
            self.stats["writes"] += 1
        else:
            self.stats["reads"] += 1

        tag, index, offset = self._decode(addr)
        line_set = self.sets[index]

        # Check for hit
        hit_way = None
        for w, line in enumerate(line_set):
            if line.valid and line.tag == tag:
                hit_way = w
                break

        result = {"hit": hit_way is not None, "way": hit_way,
                  "evicted": False, "evicted_dirty": False, "writeback": False}

        if hit_way is not None:
            self.stats["hits"] += 1
            self._touch_lru(index, hit_way)
            if is_write and self.write_back:
                line_set[hit_way].dirty = True
            # write-through mode: would push to memory here; not modeled (see docs)
        else:
            self.stats["misses"] += 1
            victim_way = self._find_victim(index)
            victim_line = line_set[victim_way]

            if victim_line.valid and victim_line.dirty:
                result["evicted"] = True
                result["evicted_dirty"] = True
                result["writeback"] = True
                self.stats["writebacks"] += 1

            # Install new line
            line_set[victim_way] = CacheLine(valid=True, dirty=False, tag=tag)
            self._touch_lru(index, victim_way)
            result["way"] = victim_way

            if is_write and self.write_back:
                line_set[victim_way].dirty = True

        return result

    def hit_rate(self) -> float:
        if self.stats["accesses"] == 0:
            return 0.0
        return self.stats["hits"] / self.stats["accesses"]

    def miss_rate(self) -> float:
        return 1.0 - self.hit_rate()


if __name__ == "__main__":
    # Quick self-test: direct-mapped, 4 lines, verify basic hit/miss/eviction behavior
    cache = GoldenCache(cache_size_bytes=128, line_size_bytes=32, associativity=1, write_back=True)
    print(f"num_sets={cache.num_sets}, offset_bits={cache.offset_bits}, index_bits={cache.index_bits}, tag_bits={cache.tag_bits}")

    print(cache.access(0x00, False))   # miss (cold)
    print(cache.access(0x00, False))   # hit
    print(cache.access(0x00, True))    # hit, write -> dirty
    print(cache.access(0x80, False))   # miss, evicts set 0's line (dirty) -> writeback
    print(f"hit_rate={cache.hit_rate():.2f}, stats={cache.stats}")