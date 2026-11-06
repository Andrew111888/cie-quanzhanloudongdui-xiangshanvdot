// Two-stage arithmetic experiment: nine terms compressed before one final add.
module VdotAccCsa(
  input clock,
  input enable1,
  input enable2,
  input [127:0] vs1,
  input [127:0] vs2,
  input [31:0] acc,
  output [127:0] result
);
  reg [15:0] products [0:7];
  reg [31:0] acc_q;
  reg [31:0] result_q;
  wire [31:0] terms [0:8];
  wire [31:0] level1 [0:5];
  wire [31:0] level2 [0:3];
  wire [31:0] level3 [0:2];
  wire [31:0] level4 [0:1];
  function [31:0] carry;
    input [31:0] a,b,c;
    begin carry = ((a & b) | (a & c) | (b & c)) << 1; end
  endfunction
  genvar lane;
  generate
    for (lane=0;lane<8;lane=lane+1) begin: extend_product
      assign terms[lane] = {{16{products[lane][15]}},products[lane]};
    end
    for (lane=0;lane<3;lane=lane+1) begin: compress1
      assign level1[2*lane] = terms[3*lane] ^ terms[3*lane+1] ^ terms[3*lane+2];
      assign level1[2*lane+1] = carry(terms[3*lane],terms[3*lane+1],terms[3*lane+2]);
    end
    for (lane=0;lane<2;lane=lane+1) begin: compress2
      assign level2[2*lane] = level1[3*lane] ^ level1[3*lane+1] ^ level1[3*lane+2];
      assign level2[2*lane+1] = carry(level1[3*lane],level1[3*lane+1],level1[3*lane+2]);
    end
  endgenerate
  assign terms[8] = acc_q;
  assign level3[0] = level2[0] ^ level2[1] ^ level2[2];
  assign level3[1] = carry(level2[0],level2[1],level2[2]);
  assign level3[2] = level2[3];
  assign level4[0] = level3[0] ^ level3[1] ^ level3[2];
  assign level4[1] = carry(level3[0],level3[1],level3[2]);
  integer i;
  always @(posedge clock) begin
    if (enable1) begin
      for (i=0;i<8;i=i+1)
        products[i] <= 16'({{8{vs1[8*i+7]}},vs1[8*i +: 8]} *
                          {{8{vs2[8*i+7]}},vs2[8*i +: 8]});
      acc_q <= acc;
    end
    if (enable2) result_q <= level4[0] + level4[1];
  end
  assign result = {96'b0,result_q};
endmodule
