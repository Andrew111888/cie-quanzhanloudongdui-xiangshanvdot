module PpaTop(
  input clock,
  input enable,
  input [127:0] vs1,
  input [127:0] vs2,
  output [127:0] result
);
  VdotPipelined4 dut(
    .clock(clock),.enable(enable),.vs1(vs1),.vs2(vs2),.result(result)
  );
endmodule
