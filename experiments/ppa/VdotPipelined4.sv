// Isolated arithmetic experiment. This module is not integrated into XiangShan.
// A shared clock enable stalls all four pipeline stages together.
module VdotPipelined4(
  input          clock,
  input          enable,
  input  [127:0] vs1,
  input  [127:0] vs2,
  output [127:0] result
);
  // Keep the multiplication expressions identical to the generated two-stage RTL.
  reg [15:0] products [0:7];
  reg signed [16:0] pairs [0:3];
  reg signed [17:0] quads [0:1];
  reg signed [18:0] total;
  integer i;
  always @(posedge clock) begin
    if (enable) begin
      for (i=0;i<8;i=i+1)
        products[i] <= 16'({{8{vs1[8*i+7]}},vs1[8*i +: 8]} *
                          {{8{vs2[8*i+7]}},vs2[8*i +: 8]});
      for (i=0;i<4;i=i+1)
        pairs[i] <= {products[2*i][15], products[2*i]} +
                    {products[2*i+1][15], products[2*i+1]};
      for (i=0;i<2;i=i+1)
        quads[i] <= {pairs[2*i][16], pairs[2*i]} +
                    {pairs[2*i+1][16], pairs[2*i+1]};
      total <= {quads[0][17], quads[0]} + {quads[1][17], quads[1]};
    end
  end
  assign result = {96'b0, {13{total[18]}}, total};
endmodule
