`timescale 1ns/1ps

// Tag array: stores tag, valid, and dirty bits for every line in the
// cache, and performs hit detection (compares the incoming tag against
// all ways in the addressed set, in parallel, as real set-associative
// caches do).
module cache_tagarray #(
    parameter NUM_SETS      = 32,
    parameter ASSOCIATIVITY = 4,
    parameter TAG_BITS      = 20,
    parameter WAY_BITS      = 2
)(
    input  wire                          clk,
    input  wire                          rst_n,

    input  wire [$clog2(NUM_SETS)-1:0]   set_idx,
    input  wire [TAG_BITS-1:0]           tag_in,

    // Hit detection (combinational, based on current state)
    output wire                          hit,
    output wire [WAY_BITS-1:0]           hit_way,

    // Fill (on a miss, after the line is fetched): write a new tag into
    // a specific way, mark valid, clear dirty (fresh clean line)
    input  wire                          fill_en,
    input  wire [WAY_BITS-1:0]           fill_way,
    input  wire [TAG_BITS-1:0]           fill_tag,

    // Write-hit dirty marking (write-back mode only): mark a way dirty
    // when a write hits it
    input  wire                          set_dirty_en,
    input  wire [WAY_BITS-1:0]           set_dirty_way,

    // Eviction query: read out the tag/valid/dirty of a specific way in
    // a specific set, used by the controller to decide whether an
    // eviction requires a write-back
    input  wire [$clog2(NUM_SETS)-1:0]   evict_set,
    input  wire [WAY_BITS-1:0]           evict_way,
    output wire [TAG_BITS-1:0]           evict_tag,
    output wire                          evict_valid,
    output wire                          evict_dirty
);

    reg [TAG_BITS-1:0] tag_mem   [0:NUM_SETS-1][0:ASSOCIATIVITY-1];
    reg                 valid_mem [0:NUM_SETS-1][0:ASSOCIATIVITY-1];
    reg                 dirty_mem [0:NUM_SETS-1][0:ASSOCIATIVITY-1];

    integer s, w;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (s = 0; s < NUM_SETS; s = s + 1) begin
                for (w = 0; w < ASSOCIATIVITY; w = w + 1) begin
                    valid_mem[s][w] <= 1'b0;
                    dirty_mem[s][w] <= 1'b0;
                    tag_mem[s][w]   <= {TAG_BITS{1'b0}};
                end
            end
                    end else begin
            if (fill_en) begin
                tag_mem[set_idx][fill_way]   <= fill_tag;
                valid_mem[set_idx][fill_way] <= 1'b1;
                // Dirty defaults to clean on fill, UNLESS this same cycle also
                // requests marking it dirty (write-miss fill case) - checked
                // explicitly here rather than relying on statement order between
                // this block and the set_dirty_en block below, since both target
                // the same dirty_mem location when a write-miss fill happens.
                dirty_mem[set_idx][fill_way] <= (set_dirty_en && (set_dirty_way == fill_way)) ? 1'b1 : 1'b0;
            end
            if (set_dirty_en && !(fill_en && (set_dirty_way == fill_way))) begin
                dirty_mem[set_idx][set_dirty_way] <= 1'b1;
            end
        end
    end

    // Combinational hit detection: compare tag_in against every way in set_idx
    reg                 hit_comb;
    reg [WAY_BITS-1:0]  hit_way_comb;

    always @(*) begin
        hit_comb     = 1'b0;
        hit_way_comb = {WAY_BITS{1'b0}};
        for (w = 0; w < ASSOCIATIVITY; w = w + 1) begin
            if (valid_mem[set_idx][w] && (tag_mem[set_idx][w] == tag_in)) begin
                hit_comb     = 1'b1;
                hit_way_comb = w[WAY_BITS-1:0];
            end
        end
    end

    assign hit     = hit_comb;
    assign hit_way = hit_way_comb;

    assign evict_tag   = tag_mem[evict_set][evict_way];
    assign evict_valid = valid_mem[evict_set][evict_way];
    assign evict_dirty = dirty_mem[evict_set][evict_way];

endmodule