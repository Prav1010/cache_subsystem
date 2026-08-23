`timescale 1ns/1ps

// LRU (Least Recently Used) replacement policy tracker, generic across
// any associativity. Uses an age-counter scheme (not a pseudo-LRU
// approximation): each way within a set has an AGE_BITS-wide age
// counter. On every access to a set, the accessed way's counter resets
// to 0 (most recently used) and every other way's counter increments
// by 1 (up to a saturating max). The eviction victim on a miss is
// whichever way currently has the highest age counter value.
//
// This is exact LRU, not an approximation - chosen for correctness and
// ease of verification against the Python golden model, at the cost of
// needing AGE_BITS*ASSOCIATIVITY bits of state per set rather than the
// fewer bits a pseudo-LRU tree would need. See docs/design_choices.md
// for the trade-off discussion (exact LRU vs. pseudo-LRU / tree-LRU).
module cache_lru #(
    parameter NUM_SETS      = 32,
    parameter ASSOCIATIVITY = 4,
    parameter WAY_BITS      = 2
)(
    input  wire                          clk,
    input  wire                          rst_n,

    input  wire                          access_valid,   // pulse: an access (hit or fill) happened this cycle
    input  wire [$clog2(NUM_SETS)-1:0]   access_set,
    input  wire [WAY_BITS-1:0]           access_way,     // which way was hit or filled

    input  wire [$clog2(NUM_SETS)-1:0]   victim_set,     // set being queried for eviction victim
    output wire [WAY_BITS-1:0]           victim_way      // way with the highest age in victim_set (LRU choice)
);

    localparam AGE_BITS = $clog2(ASSOCIATIVITY) + 1; // enough to count 0..ASSOCIATIVITY-1 plus headroom

    // age[set][way]
    reg [AGE_BITS-1:0] age [0:NUM_SETS-1][0:ASSOCIATIVITY-1];

    integer s, w;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (s = 0; s < NUM_SETS; s = s + 1) begin
                for (w = 0; w < ASSOCIATIVITY; w = w + 1) begin
                    age[s][w] <= w[AGE_BITS-1:0]; // distinct initial ages so victim selection is deterministic before any access
                end
            end
        end else if (access_valid) begin
            for (w = 0; w < ASSOCIATIVITY; w = w + 1) begin
                if (w[WAY_BITS-1:0] == access_way) begin
                    age[access_set][w] <= {AGE_BITS{1'b0}}; // accessed way becomes most-recently-used
                end else if (age[access_set][w] < {AGE_BITS{1'b1}}) begin
                    age[access_set][w] <= age[access_set][w] + 1'b1; // age everyone else
                end
            end
        end
    end

    // Combinational victim selection: find the way with the maximum age in victim_set
    reg [WAY_BITS-1:0] victim_way_comb;
    reg [AGE_BITS-1:0] max_age_comb;

    always @(*) begin
        victim_way_comb = {WAY_BITS{1'b0}};
        max_age_comb    = {AGE_BITS{1'b0}};
        for (w = 0; w < ASSOCIATIVITY; w = w + 1) begin
            if (age[victim_set][w] >= max_age_comb) begin
                max_age_comb    = age[victim_set][w];
                victim_way_comb = w[WAY_BITS-1:0];
            end
        end
    end

    assign victim_way = victim_way_comb;

endmodule