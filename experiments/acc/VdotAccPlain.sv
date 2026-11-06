// Two-stage arithmetic experiment: binary sum tree followed by accumulator add.
module VdotAccPlain(
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
  wire [16:0] pairs [0:3];
  wire [17:0] quads [0:1];
  wire [18:0] sum;
  genvar lane;
  generate
    for (lane=0;lane<4;lane=lane+1) begin: pair_sum
      assign pairs[lane] = {products[2*lane][15],products[2*lane]} +
                           {products[2*lane+1][15],products[2*lane+1]};
    end
    for (lane=0;lane<2;lane=lane+1) begin: quad_sum
      assign quads[lane] = {pairs[2*lane][16],pairs[2*lane]} +
                           {pairs[2*lane+1][16],pairs[2*lane+1]};
    end
  endgenerate
  assign sum = {quads[0][17],quads[0]} + {quads[1][17],quads[1]};
  integer i;
  always @(posedge clock) begin
    if (enable1) begin
      for (i=0;i<8;i=i+1)
        products[i] <= 16'({{8{vs1[8*i+7]}},vs1[8*i +: 8]} *
                          {{8{vs2[8*i+7]}},vs2[8*i +: 8]});
      acc_q <= acc;
    end
    if (enable2) result_q <= {{13{sum[18]}},sum} + acc_q;
  end
  assign result = {96'b0,result_q};
endmodule
