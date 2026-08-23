`timescale 1ns/1ps

// Data array: stores the actual cache line data. One line per
// (set, way) pair, LINE_SIZE_BYTES wide. Supports full-line fill
// (on a miss, after fetching from memory) and byte-level write
// (on a write hit, writing only the specific byte(s) being written).
module cache_dataarray #(
    parameter NUM_SETS       = 32,
    parameter ASSOCIATIVITY  = 4,
    parameter LINE_SIZE_BYTES = 32,
    parameter WAY_BITS       = 2
)(
    input  wire                                 clk,

    input  wire [$clog2(NUM_SETS)-1:0]          set_idx,
    input  wire [WAY_BITS-1:0]                  way_idx,

    // Read: combinational read of the full line at (set_idx, way_idx)
    output wire [LINE_SIZE_BYTES*8-1:0]         read_line,

    // Full-line fill (on a miss, writing an entire fetched line)
    input  wire                                 fill_en,
    input  wire [LINE_SIZE_BYTES*8-1:0]         fill_data,

    // Byte-level write (on a write hit, in either write-through or
    // write-back mode - only the addressed byte(s) within the line change)
    input  wire                                 byte_write_en,
    input  wire [$clog2(LINE_SIZE_BYTES)-1:0]   byte_offset,
    input  wire [7:0]                           write_byte_data
);

    // mem[set][way] is a LINE_SIZE_BYTES*8-bit line
    reg [LINE_SIZE_BYTES*8-1:0] mem [0:NUM_SETS-1][0:ASSOCIATIVITY-1];

    always @(posedge clk) begin
        if (fill_en) begin
            mem[set_idx][way_idx] <= fill_data;
        end else if (byte_write_en) begin
            mem[set_idx][way_idx][byte_offset*8 +: 8] <= write_byte_data;
        end
    end

    assign read_line = mem[set_idx][way_idx];

endmodule