// Retimed candidate: first 3:2 compression shares the multiplication stage.
module VdotAccRetimed(
  input clock,
  input enable1,
  input enable2,
  input [127:0] vs1,
  input [127:0] vs2,
  input [31:0] acc,
  output [127:0] result
);
  wire [15:0] products [0:7];
  reg [31:0] result_q;
  wire [31:0] terms [0:8];
  reg [31:0] level1 [0:5];
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
      assign products[lane] = 16'({{8{vs1[8*lane+7]}},vs1[8*lane +: 8]} *
                                  {{8{vs2[8*lane+7]}},vs2[8*lane +: 8]});
      assign terms[lane] = {{16{products[lane][15]}},products[lane]};
    end
    for (lane=0;lane<2;lane=lane+1) begin: compress2
      assign level2[2*lane] = level1[3*lane] ^ level1[3*lane+1] ^ level1[3*lane+2];
      assign level2[2*lane+1] = carry(level1[3*lane],level1[3*lane+1],level1[3*lane+2]);
    end
  endgenerate
  assign terms[8] = acc;
  assign level3[0] = level2[0] ^ level2[1] ^ level2[2];
  assign level3[1] = carry(level2[0],level2[1],level2[2]);
  assign level3[2] = level2[3];
  assign level4[0] = level3[0] ^ level3[1] ^ level3[2];
  assign level4[1] = carry(level3[0],level3[1],level3[2]);
  wire [31:0] propagate [0:5];
  wire [31:0] generate_bit [0:5];
  wire [31:0] prefix_sum;
  assign propagate[0] = level4[0] ^ level4[1];
  assign generate_bit[0] = level4[0] & level4[1];
  genvar level, bit_index;
  generate
    for (level=0;level<5;level=level+1) begin: prefix_level
      for (bit_index=0;bit_index<32;bit_index=bit_index+1) begin: prefix_bit
        if (bit_index >= (1 << level)) begin: combine
          assign generate_bit[level+1][bit_index] = generate_bit[level][bit_index] |
            (propagate[level][bit_index] & generate_bit[level][bit_index-(1 << level)]);
          assign propagate[level+1][bit_index] = propagate[level][bit_index] &
            propagate[level][bit_index-(1 << level)];
        end else begin: pass
          assign generate_bit[level+1][bit_index] = generate_bit[level][bit_index];
          assign propagate[level+1][bit_index] = propagate[level][bit_index];
        end
      end
    end
  endgenerate
  assign prefix_sum = propagate[0] ^ {generate_bit[5][30:0],1'b0};
  integer i;
  always @(posedge clock) begin
    if (enable1) begin
      for (i=0;i<3;i=i+1) begin
        level1[2*i] <= terms[3*i] ^ terms[3*i+1] ^ terms[3*i+2];
        level1[2*i+1] <= carry(terms[3*i],terms[3*i+1],terms[3*i+2]);
      end
    end
    if (enable2) result_q <= prefix_sum;
  end
  assign result = {96'b0,result_q};
endmodule
