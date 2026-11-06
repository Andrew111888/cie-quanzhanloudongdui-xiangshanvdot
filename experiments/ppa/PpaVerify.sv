module PpaVerify(
  input clock,
  input enable,
  input [127:0] vs1,
  input [127:0] vs2,
  output [127:0] result2,
  output [127:0] result4
);
  VdotDatapath a(.clock(clock),.io_enable1(enable),.io_enable2(enable),
                .io_vs1(vs1),.io_vs2(vs2),.io_result(result2));
  VdotPipelined4 b(.clock(clock),.enable(enable),.vs1(vs1),.vs2(vs2),.result(result4));
endmodule
