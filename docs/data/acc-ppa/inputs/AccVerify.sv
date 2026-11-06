module AccVerify(
  input clock,
  input enable1,
  input enable2,
  input [127:0] vs1,
  input [127:0] vs2,
  input [31:0] acc,
  output [127:0] result_plain,
  output [127:0] result_csa,
  output [127:0] result_prefix,
  output [127:0] result_prefix_or,
  output [127:0] result_retimed,
  output [127:0] result_chisel_retimed,
  output [127:0] result_chisel_prefix,
  output [127:0] result_chisel_plain,
  output [127:0] result_chisel_csa,
  output [127:0] result_original
);
  VdotAccPlain plain(.clock(clock),.enable1(enable1),.enable2(enable2),.vs1(vs1),.vs2(vs2),.acc(acc),.result(result_plain));
  VdotAccCsa csa(.clock(clock),.enable1(enable1),.enable2(enable2),.vs1(vs1),.vs2(vs2),.acc(acc),.result(result_csa));
  VdotAccCsaPrefix prefix(.clock(clock),.enable1(enable1),.enable2(enable2),.vs1(vs1),.vs2(vs2),.acc(acc),.result(result_prefix));
  VdotAccRetimed retimed(.clock(clock),.enable1(enable1),.enable2(enable2),.vs1(vs1),.vs2(vs2),.acc(acc),.result(result_retimed));
  VdotAccCsaPrefixOr prefix_or(.clock(clock),.enable1(enable1),.enable2(enable2),.vs1(vs1),.vs2(vs2),.acc(acc),.result(result_prefix_or));
`ifdef ACC_WITH_CHISEL_RETIMED
  VdotAccRetimedDatapath chisel_retimed(.clock(clock),.reset(1'b0),.io_enable1(enable1),.io_enable2(enable2),.io_vs1(vs1),.io_vs2(vs2),.io_acc(acc),.io_result(result_chisel_retimed));
`else
  assign result_chisel_retimed = result_retimed;
`endif
`ifdef ACC_WITH_CHISEL_PREFIX
  VdotAccCsaPrefixDatapath chisel_prefix(.clock(clock),.reset(1'b0),.io_enable1(enable1),.io_enable2(enable2),.io_vs1(vs1),.io_vs2(vs2),.io_acc(acc),.io_result(result_chisel_prefix));
`else
  assign result_chisel_prefix = result_prefix;
`endif
`ifdef ACC_WITH_CHISEL
  VdotAccPlainDatapath chisel_plain(.clock(clock),.reset(1'b0),.io_enable1(enable1),.io_enable2(enable2),.io_vs1(vs1),.io_vs2(vs2),.io_acc(acc),.io_result(result_chisel_plain));
  VdotAccCsaDatapath chisel_csa(.clock(clock),.reset(1'b0),.io_enable1(enable1),.io_enable2(enable2),.io_vs1(vs1),.io_vs2(vs2),.io_acc(acc),.io_result(result_chisel_csa));
`else
  assign result_chisel_plain = result_plain;
  assign result_chisel_csa = result_csa;
`endif
  VdotDatapath original(.clock(clock),.io_enable1(enable1),.io_enable2(enable2),.io_vs1(vs1),.io_vs2(vs2),.io_result(result_original));
endmodule
