// SPDX-License-Identifier: MulanPSL-2.0
// Experimental elastic wrapper; it does not replace the processor's VIMacU.
module IsolationCompare(
  input clock, reset, flush,
  input in_valid, in_dot, in_acc, out_ready,
  input [127:0] vs1, vs2,
  input [31:0] acc,
  input [31:0] in_tag,
  output in_ready, out_valid, out_dot,
  output isolated_enable1, isolated_enable2,
  output [31:0] out_tag,
  output [127:0] baseline_result, isolated_result,
  output [127:0] baseline_products, isolated_products,
  output [191:0] baseline_stage1, isolated_stage1,
  output [31:0] baseline_dot_result, isolated_dot_result
);
  reg valid1, valid2, dot1, dot2;
  reg [31:0] tag1, tag2;
  reg [127:0] standard1, standard2;
  wire advance2 = !valid2 || out_ready;
  wire advance1 = !valid1 || advance2;
  wire accept = in_valid && advance1 && !flush && !reset;
  wire move = valid1 && advance2 && !flush && !reset;
  assign in_ready = advance1 && !flush && !reset;
  assign out_valid = valid2 && !flush && !reset;
  assign out_dot = dot2;
  assign out_tag = tag2;
  assign isolated_enable1 = accept && in_dot;
  assign isolated_enable2 = move && dot1;
  // An independent lane-wise 8-bit multiply provides changing non-dot traffic.
  // This simple side path is a harness model, not the standard VIMac64b RTL.
  wire [127:0] standard_next;
  genvar i;
  generate for(i=0;i<16;i=i+1) begin
    assign standard_next[i*8 +: 8] = vs1[i*8 +: 8] * vs2[i*8 +: 8];
  end endgenerate
  always @(posedge clock) begin
    if(reset || flush) begin valid1<=0;valid2<=0;dot1<=0;dot2<=0;end
    else begin
      if(advance2) begin
        valid2<=valid1;
        if(valid1) begin dot2<=dot1;tag2<=tag1;standard2<=standard1;end
      end
      if(advance1) begin
        valid1<=in_valid;
        if(in_valid) begin dot1<=in_dot;tag1<=in_tag;standard1<=standard_next;end
      end
    end
  end
  wire [127:0] baseline_dot, isolated_dot;
  wire select_dot = in_valid && in_dot && !flush && !reset;
  VdotAccRetimedDatapath baseline(
    .clock(clock),.io_vs1(vs1),.io_vs2(vs2),.io_acc(in_acc ? acc : 32'b0),
    .io_enable1(accept),.io_enable2(move),.io_result(baseline_dot));
  VdotAccRetimedDatapath isolated(
    .clock(clock),.io_vs1(select_dot ? vs1 : 128'b0),.io_vs2(select_dot ? vs2 : 128'b0),
    .io_acc(select_dot && in_acc ? acc : 32'b0),
    .io_enable1(accept && in_dot),.io_enable2(move && dot1),.io_result(isolated_dot));
  assign baseline_result = dot2 ? baseline_dot : standard2;
  assign isolated_result = dot2 ? isolated_dot : standard2;
  assign baseline_products = {baseline.inputProducts_7,baseline.inputProducts_6,baseline.inputProducts_5,baseline.inputProducts_4,baseline.inputProducts_3,baseline.inputProducts_2,baseline.inputProducts_1,baseline.inputProducts_0};
  assign isolated_products = {isolated.inputProducts_7,isolated.inputProducts_6,isolated.inputProducts_5,isolated.inputProducts_4,isolated.inputProducts_3,isolated.inputProducts_2,isolated.inputProducts_1,isolated.inputProducts_0};
  assign baseline_stage1={baseline.nextResult_level1_5,baseline.nextResult_level1_4,baseline.nextResult_level1_3,baseline.nextResult_level1_2,baseline.nextResult_level1_1,baseline.nextResult_level1_0};
  assign isolated_stage1={isolated.nextResult_level1_5,isolated.nextResult_level1_4,isolated.nextResult_level1_3,isolated.nextResult_level1_2,isolated.nextResult_level1_1,isolated.nextResult_level1_0};
  assign baseline_dot_result=baseline_dot[31:0];
  assign isolated_dot_result=isolated_dot[31:0];
endmodule
