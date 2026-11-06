module VdotAccPlainDatapath( // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 47:7]
  input          clock, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 47:7]
  input          reset, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 47:7]
  input  [127:0] io_vs1, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 51:14]
  input  [127:0] io_vs2, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 51:14]
  input  [31:0]  io_acc, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 51:14]
  input          io_enable1, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 51:14]
  input          io_enable2, // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 51:14]
  output [127:0] io_result // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 51:14]
);
`ifdef RANDOMIZE_REG_INIT
  reg [31:0] _RAND_0;
  reg [31:0] _RAND_1;
  reg [31:0] _RAND_2;
  reg [31:0] _RAND_3;
  reg [31:0] _RAND_4;
  reg [31:0] _RAND_5;
  reg [31:0] _RAND_6;
  reg [31:0] _RAND_7;
  reg [31:0] _RAND_8;
  reg [31:0] _RAND_9;
`endif // RANDOMIZE_REG_INIT
  wire [7:0] _inputProducts_0_T_1 = io_vs1[7:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_0_T_3 = io_vs2[7:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_0 = $signed(_inputProducts_0_T_1) * $signed(_inputProducts_0_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_1_T_1 = io_vs1[15:8]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_1_T_3 = io_vs2[15:8]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_1 = $signed(_inputProducts_1_T_1) * $signed(_inputProducts_1_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_2_T_1 = io_vs1[23:16]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_2_T_3 = io_vs2[23:16]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_2 = $signed(_inputProducts_2_T_1) * $signed(_inputProducts_2_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_3_T_1 = io_vs1[31:24]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_3_T_3 = io_vs2[31:24]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_3 = $signed(_inputProducts_3_T_1) * $signed(_inputProducts_3_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_4_T_1 = io_vs1[39:32]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_4_T_3 = io_vs2[39:32]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_4 = $signed(_inputProducts_4_T_1) * $signed(_inputProducts_4_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_5_T_1 = io_vs1[47:40]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_5_T_3 = io_vs2[47:40]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_5 = $signed(_inputProducts_5_T_1) * $signed(_inputProducts_5_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_6_T_1 = io_vs1[55:48]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_6_T_3 = io_vs2[55:48]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_6 = $signed(_inputProducts_6_T_1) * $signed(_inputProducts_6_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  wire [7:0] _inputProducts_7_T_1 = io_vs1[63:56]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:44]
  wire [7:0] _inputProducts_7_T_3 = io_vs2[63:56]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:72]
  wire [15:0] inputProducts_7 = $signed(_inputProducts_7_T_1) * $signed(_inputProducts_7_T_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 61:51]
  reg [15:0] nextResult_products_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_2; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_3; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_4; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_6; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [15:0] nextResult_products_7; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 100:23]
  reg [31:0] nextResult_accumulator; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 101:26]
  wire [16:0] nextResult_pairs_0 = $signed(nextResult_products_0) + $signed(nextResult_products_1); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 107:54]
  wire [16:0] nextResult_pairs_1 = $signed(nextResult_products_2) + $signed(nextResult_products_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 107:54]
  wire [16:0] nextResult_pairs_2 = $signed(nextResult_products_4) + $signed(nextResult_products_5); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 107:54]
  wire [16:0] nextResult_pairs_3 = $signed(nextResult_products_6) + $signed(nextResult_products_7); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 107:54]
  wire [17:0] nextResult_quads_0 = $signed(nextResult_pairs_0) + $signed(nextResult_pairs_1); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 108:51]
  wire [17:0] nextResult_quads_1 = $signed(nextResult_pairs_2) + $signed(nextResult_pairs_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 108:51]
  wire [18:0] nextResult_sum = $signed(nextResult_quads_0) + $signed(nextResult_quads_1); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 109:26]
  wire [31:0] _nextResult_T_1 = {{13{nextResult_sum[18]}},nextResult_sum}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 110:19]
  wire [31:0] nextResult = _nextResult_T_1 + nextResult_accumulator; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 110:26]
  reg [31:0] result; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 113:19]
  assign io_result = {96'h0,result}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 115:19]
  always @(posedge clock) begin
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_0 <= inputProducts_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_1 <= inputProducts_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_2 <= inputProducts_2; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_3 <= inputProducts_3; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_4 <= inputProducts_4; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_5 <= inputProducts_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_6 <= inputProducts_6; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_products_7 <= inputProducts_7; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:33]
    end
    if (io_enable1) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:22]
      nextResult_accumulator <= io_acc; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 102:63]
    end
    if (io_enable2) begin // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 114:20]
      result <= nextResult; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 114:29]
    end
  end
// Register and memory initialization
`ifdef RANDOMIZE_GARBAGE_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_INVALID_ASSIGN
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_REG_INIT
`define RANDOMIZE
`endif
`ifdef RANDOMIZE_MEM_INIT
`define RANDOMIZE
`endif
`ifndef RANDOM
`define RANDOM $random
`endif
`ifdef RANDOMIZE_MEM_INIT
  integer initvar;
`endif
`ifndef SYNTHESIS
`ifdef FIRRTL_BEFORE_INITIAL
`FIRRTL_BEFORE_INITIAL
`endif
initial begin
  `ifdef RANDOMIZE
    `ifdef INIT_RANDOM
      `INIT_RANDOM
    `endif
    `ifndef VERILATOR
      `ifdef RANDOMIZE_DELAY
        #`RANDOMIZE_DELAY begin end
      `else
        #0.002 begin end
      `endif
    `endif
`ifdef RANDOMIZE_REG_INIT
  _RAND_0 = {1{`RANDOM}};
  nextResult_products_0 = _RAND_0[15:0];
  _RAND_1 = {1{`RANDOM}};
  nextResult_products_1 = _RAND_1[15:0];
  _RAND_2 = {1{`RANDOM}};
  nextResult_products_2 = _RAND_2[15:0];
  _RAND_3 = {1{`RANDOM}};
  nextResult_products_3 = _RAND_3[15:0];
  _RAND_4 = {1{`RANDOM}};
  nextResult_products_4 = _RAND_4[15:0];
  _RAND_5 = {1{`RANDOM}};
  nextResult_products_5 = _RAND_5[15:0];
  _RAND_6 = {1{`RANDOM}};
  nextResult_products_6 = _RAND_6[15:0];
  _RAND_7 = {1{`RANDOM}};
  nextResult_products_7 = _RAND_7[15:0];
  _RAND_8 = {1{`RANDOM}};
  nextResult_accumulator = _RAND_8[31:0];
  _RAND_9 = {1{`RANDOM}};
  result = _RAND_9[31:0];
`endif // RANDOMIZE_REG_INIT
  `endif // RANDOMIZE
end // initial
`ifdef FIRRTL_AFTER_INITIAL
`FIRRTL_AFTER_INITIAL
`endif
`endif // SYNTHESIS
endmodule
