# Vivado out-of-context synthesis script for cache_subsystem
# Run from the synth/ directory:
#   vivado -mode batch -source cache_synth.tcl

set part_name    "xc7a35tcpg236-1"   ;# Artix-7 (Basys3-class part)
set rtl_dir      "../rtl"
set report_dir   "./reports"
set gates_dir    "./gates"

file mkdir $report_dir
file mkdir $gates_dir

# Read RTL sources (order matters: package/interface first, then submodules, then top)
read_verilog -sv $rtl_dir/cache_config_pkg.sv
read_verilog -sv $rtl_dir/cache_interface.sv
read_verilog -sv $rtl_dir/cache_lru.v
read_verilog -sv $rtl_dir/cache_tagarray.v
read_verilog -sv $rtl_dir/cache_dataarray.v
read_verilog -sv $rtl_dir/cache_controller.v

# Set the top module
set_property top cache_controller [current_fileset]

# Synthesize out-of-context (standalone block synthesis, no I/O buffers)
synth_design -top cache_controller -part $part_name -mode out_of_context

# Generate reports
report_utilization             -file $report_dir/area_breakdown.rpt
report_timing_summary          -file $report_dir/timing.rpt
report_timing -delay_type max -max_paths 10 -file $report_dir/timing_max_paths.rpt
report_power                   -file $report_dir/power_breakdown.rpt

puts "=== Synthesis complete ==="
puts "Reports written to $report_dir/"

# Write out the synthesized netlist and checkpoint for reference
write_verilog -force $gates_dir/cache_controller_synth.v
write_checkpoint -force $gates_dir/cache_controller_post_synth.dcp