`timescale 1ns/1ps

// Request/response type definitions for the cache subsystem.
// Kept as a separate package (rather than a SystemVerilog `interface`)
// for maximum tool compatibility, since not every simulator/synthesis
// flow supports SV interfaces equally well - plain structs work
// everywhere and are simple to trace in waveforms.
package cache_interface_pkg;

    typedef enum logic [1:0] {
        REQ_NONE  = 2'b00,
        REQ_READ  = 2'b01,
        REQ_WRITE = 2'b10
    } req_type_e;

    typedef enum logic [1:0] {
        RESP_NONE = 2'b00,
        RESP_HIT  = 2'b01,
        RESP_MISS = 2'b10,
        RESP_BUSY = 2'b11   // request cannot be accepted this cycle (miss being serviced)
    } resp_type_e;

endpackage