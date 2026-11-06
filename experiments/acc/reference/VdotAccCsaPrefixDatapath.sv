module VdotAccCsaPrefixDatapath( // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 47:7]
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
  wire [31:0] _nextResult_terms_T_1 = {{16{nextResult_products_0[15]}},nextResult_products_0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_3 = {{16{nextResult_products_1[15]}},nextResult_products_1}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_5 = {{16{nextResult_products_2[15]}},nextResult_products_2}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_7 = {{16{nextResult_products_3[15]}},nextResult_products_3}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_9 = {{16{nextResult_products_4[15]}},nextResult_products_4}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_11 = {{16{nextResult_products_5[15]}},nextResult_products_5}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_13 = {{16{nextResult_products_6[15]}},nextResult_products_6}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_T_15 = {{16{nextResult_products_7[15]}},nextResult_products_7}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 104:57]
  wire [31:0] _nextResult_terms_majority_T = _nextResult_terms_T_1 & _nextResult_terms_T_3; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_1 = _nextResult_terms_T_1 & _nextResult_terms_T_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_2 = _nextResult_terms_majority_T | _nextResult_terms_majority_T_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_3 = _nextResult_terms_T_3 & _nextResult_terms_T_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority = _nextResult_terms_majority_T_2 | _nextResult_terms_majority_T_3; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_16 = _nextResult_terms_T_1 ^ _nextResult_terms_T_3; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] _nextResult_terms_T_17 = _nextResult_terms_T_16 ^ _nextResult_terms_T_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_18 = {nextResult_terms_majority, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] _nextResult_terms_majority_T_4 = _nextResult_terms_T_7 & _nextResult_terms_T_9; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_5 = _nextResult_terms_T_7 & _nextResult_terms_T_11; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_6 = _nextResult_terms_majority_T_4 | _nextResult_terms_majority_T_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_7 = _nextResult_terms_T_9 & _nextResult_terms_T_11; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority_1 = _nextResult_terms_majority_T_6 | _nextResult_terms_majority_T_7; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_20 = _nextResult_terms_T_7 ^ _nextResult_terms_T_9; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] _nextResult_terms_T_21 = _nextResult_terms_T_20 ^ _nextResult_terms_T_11; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_22 = {nextResult_terms_majority_1, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] _nextResult_terms_majority_T_8 = _nextResult_terms_T_13 & _nextResult_terms_T_15; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_9 = _nextResult_terms_T_13 & nextResult_accumulator; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_10 = _nextResult_terms_majority_T_8 | _nextResult_terms_majority_T_9; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_11 = _nextResult_terms_T_15 & nextResult_accumulator; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority_2 = _nextResult_terms_majority_T_10 | _nextResult_terms_majority_T_11; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_24 = _nextResult_terms_T_13 ^ _nextResult_terms_T_15; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] _nextResult_terms_T_25 = _nextResult_terms_T_24 ^ nextResult_accumulator; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_26 = {nextResult_terms_majority_2, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] _nextResult_terms_majority_T_12 = _nextResult_terms_T_17 & _nextResult_terms_T_18[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_13 = _nextResult_terms_T_17 & _nextResult_terms_T_21; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_14 = _nextResult_terms_majority_T_12 | _nextResult_terms_majority_T_13; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_15 = _nextResult_terms_T_18[31:0] & _nextResult_terms_T_21; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority_3 = _nextResult_terms_majority_T_14 | _nextResult_terms_majority_T_15; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_28 = _nextResult_terms_T_17 ^ _nextResult_terms_T_18[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] _nextResult_terms_T_29 = _nextResult_terms_T_28 ^ _nextResult_terms_T_21; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_30 = {nextResult_terms_majority_3, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] _nextResult_terms_majority_T_16 = _nextResult_terms_T_22[31:0] & _nextResult_terms_T_25; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_17 = _nextResult_terms_T_22[31:0] & _nextResult_terms_T_26[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_18 = _nextResult_terms_majority_T_16 | _nextResult_terms_majority_T_17; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_19 = _nextResult_terms_T_25 & _nextResult_terms_T_26[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority_4 = _nextResult_terms_majority_T_18 | _nextResult_terms_majority_T_19; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_32 = _nextResult_terms_T_22[31:0] ^ _nextResult_terms_T_25; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] _nextResult_terms_T_33 = _nextResult_terms_T_32 ^ _nextResult_terms_T_26[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_34 = {nextResult_terms_majority_4, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] _nextResult_terms_majority_T_20 = _nextResult_terms_T_29 & _nextResult_terms_T_30[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_21 = _nextResult_terms_T_29 & _nextResult_terms_T_33; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_22 = _nextResult_terms_majority_T_20 | _nextResult_terms_majority_T_21; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_23 = _nextResult_terms_T_30[31:0] & _nextResult_terms_T_33; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority_5 = _nextResult_terms_majority_T_22 | _nextResult_terms_majority_T_23; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_36 = _nextResult_terms_T_29 ^ _nextResult_terms_T_30[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] _nextResult_terms_T_37 = _nextResult_terms_T_36 ^ _nextResult_terms_T_33; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_38 = {nextResult_terms_majority_5, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] _nextResult_terms_majority_T_24 = _nextResult_terms_T_37 & _nextResult_terms_T_38[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:29]
  wire [31:0] _nextResult_terms_majority_T_25 = _nextResult_terms_T_37 & _nextResult_terms_T_34[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:39]
  wire [31:0] _nextResult_terms_majority_T_26 = _nextResult_terms_majority_T_24 | _nextResult_terms_majority_T_25; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:34]
  wire [31:0] _nextResult_terms_majority_T_27 = _nextResult_terms_T_38[31:0] & _nextResult_terms_T_34[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:49]
  wire [31:0] nextResult_terms_majority_6 = _nextResult_terms_majority_T_26 | _nextResult_terms_majority_T_27; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 68:44]
  wire [31:0] _nextResult_terms_T_40 = _nextResult_terms_T_37 ^ _nextResult_terms_T_38[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:17]
  wire [31:0] nextResult_terms_0 = _nextResult_terms_T_40 ^ _nextResult_terms_T_34[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:21]
  wire [32:0] _nextResult_terms_T_41 = {nextResult_terms_majority_6, 1'h0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:36]
  wire [31:0] nextResult_terms_1 = _nextResult_terms_T_41[31:0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 69:41]
  wire [31:0] _nextResult_originalPropagate_T = nextResult_terms_0 ^ nextResult_terms_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:32]
  wire  nextResult_originalPropagate_0 = _nextResult_originalPropagate_T[0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_1 = _nextResult_originalPropagate_T[1]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_2 = _nextResult_originalPropagate_T[2]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_3 = _nextResult_originalPropagate_T[3]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_4 = _nextResult_originalPropagate_T[4]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_5 = _nextResult_originalPropagate_T[5]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_6 = _nextResult_originalPropagate_T[6]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_7 = _nextResult_originalPropagate_T[7]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_8 = _nextResult_originalPropagate_T[8]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_9 = _nextResult_originalPropagate_T[9]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_10 = _nextResult_originalPropagate_T[10]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_11 = _nextResult_originalPropagate_T[11]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_12 = _nextResult_originalPropagate_T[12]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_13 = _nextResult_originalPropagate_T[13]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_14 = _nextResult_originalPropagate_T[14]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_15 = _nextResult_originalPropagate_T[15]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_16 = _nextResult_originalPropagate_T[16]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_17 = _nextResult_originalPropagate_T[17]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_18 = _nextResult_originalPropagate_T[18]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_19 = _nextResult_originalPropagate_T[19]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_20 = _nextResult_originalPropagate_T[20]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_21 = _nextResult_originalPropagate_T[21]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_22 = _nextResult_originalPropagate_T[22]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_23 = _nextResult_originalPropagate_T[23]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_24 = _nextResult_originalPropagate_T[24]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_25 = _nextResult_originalPropagate_T[25]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_26 = _nextResult_originalPropagate_T[26]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_27 = _nextResult_originalPropagate_T[27]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_28 = _nextResult_originalPropagate_T[28]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_29 = _nextResult_originalPropagate_T[29]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_30 = _nextResult_originalPropagate_T[30]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire  nextResult_originalPropagate_31 = _nextResult_originalPropagate_T[31]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 77:37]
  wire [31:0] _nextResult_generate_T = nextResult_terms_0 & nextResult_terms_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:23]
  wire  nextResult_generate_0 = _nextResult_generate_T[0]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_1 = _nextResult_generate_T[1]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_2 = _nextResult_generate_T[2]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_3 = _nextResult_generate_T[3]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_4 = _nextResult_generate_T[4]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_5 = _nextResult_generate_T[5]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_6 = _nextResult_generate_T[6]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_7 = _nextResult_generate_T[7]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_8 = _nextResult_generate_T[8]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_9 = _nextResult_generate_T[9]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_10 = _nextResult_generate_T[10]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_11 = _nextResult_generate_T[11]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_12 = _nextResult_generate_T[12]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_13 = _nextResult_generate_T[13]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_14 = _nextResult_generate_T[14]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_15 = _nextResult_generate_T[15]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_16 = _nextResult_generate_T[16]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_17 = _nextResult_generate_T[17]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_18 = _nextResult_generate_T[18]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_19 = _nextResult_generate_T[19]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_20 = _nextResult_generate_T[20]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_21 = _nextResult_generate_T[21]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_22 = _nextResult_generate_T[22]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_23 = _nextResult_generate_T[23]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_24 = _nextResult_generate_T[24]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_25 = _nextResult_generate_T[25]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_26 = _nextResult_generate_T[26]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_27 = _nextResult_generate_T[27]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_28 = _nextResult_generate_T[28]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_29 = _nextResult_generate_T[29]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  nextResult_generate_30 = _nextResult_generate_T[30]; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 78:28]
  wire  _nextResult_T_1 = nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_63 = nextResult_originalPropagate_2 & nextResult_originalPropagate_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_64 = nextResult_originalPropagate_3 & nextResult_originalPropagate_2; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_65 = nextResult_originalPropagate_4 & nextResult_originalPropagate_3; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_66 = nextResult_originalPropagate_5 & nextResult_originalPropagate_4; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_67 = nextResult_originalPropagate_6 & nextResult_originalPropagate_5; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_68 = nextResult_originalPropagate_7 & nextResult_originalPropagate_6; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_69 = nextResult_originalPropagate_8 & nextResult_originalPropagate_7; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_70 = nextResult_originalPropagate_9 & nextResult_originalPropagate_8; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_71 = nextResult_originalPropagate_10 & nextResult_originalPropagate_9; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_72 = nextResult_originalPropagate_11 & nextResult_originalPropagate_10; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_73 = nextResult_originalPropagate_12 & nextResult_originalPropagate_11; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_74 = nextResult_originalPropagate_13 & nextResult_originalPropagate_12; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_75 = nextResult_originalPropagate_14 & nextResult_originalPropagate_13; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_76 = nextResult_originalPropagate_15 & nextResult_originalPropagate_14; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_77 = nextResult_originalPropagate_16 & nextResult_originalPropagate_15; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_78 = nextResult_originalPropagate_17 & nextResult_originalPropagate_16; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_79 = nextResult_originalPropagate_18 & nextResult_originalPropagate_17; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_80 = nextResult_originalPropagate_19 & nextResult_originalPropagate_18; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_81 = nextResult_originalPropagate_20 & nextResult_originalPropagate_19; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_82 = nextResult_originalPropagate_21 & nextResult_originalPropagate_20; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_83 = nextResult_originalPropagate_22 & nextResult_originalPropagate_21; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_84 = nextResult_originalPropagate_23 & nextResult_originalPropagate_22; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_85 = nextResult_originalPropagate_24 & nextResult_originalPropagate_23; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_86 = nextResult_originalPropagate_25 & nextResult_originalPropagate_24; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_87 = nextResult_originalPropagate_26 & nextResult_originalPropagate_25; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_88 = nextResult_originalPropagate_27 & nextResult_originalPropagate_26; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_89 = nextResult_originalPropagate_28 & nextResult_originalPropagate_27; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_90 = nextResult_originalPropagate_29 & nextResult_originalPropagate_28; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_91 = nextResult_originalPropagate_30 & nextResult_originalPropagate_29; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_94 = nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1 |
    _nextResult_T_63 & nextResult_generate_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_96 = nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2 |
    _nextResult_T_64 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_155 = nextResult_originalPropagate_4 & nextResult_originalPropagate_3 & (
    nextResult_originalPropagate_2 & nextResult_originalPropagate_1); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_156 = nextResult_originalPropagate_5 & nextResult_originalPropagate_4 & (
    nextResult_originalPropagate_3 & nextResult_originalPropagate_2); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_157 = nextResult_originalPropagate_6 & nextResult_originalPropagate_5 & (
    nextResult_originalPropagate_4 & nextResult_originalPropagate_3); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_158 = nextResult_originalPropagate_7 & nextResult_originalPropagate_6 & (
    nextResult_originalPropagate_5 & nextResult_originalPropagate_4); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_159 = nextResult_originalPropagate_8 & nextResult_originalPropagate_7 & (
    nextResult_originalPropagate_6 & nextResult_originalPropagate_5); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_160 = nextResult_originalPropagate_9 & nextResult_originalPropagate_8 & (
    nextResult_originalPropagate_7 & nextResult_originalPropagate_6); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_161 = nextResult_originalPropagate_10 & nextResult_originalPropagate_9 & (
    nextResult_originalPropagate_8 & nextResult_originalPropagate_7); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_162 = nextResult_originalPropagate_11 & nextResult_originalPropagate_10 & (
    nextResult_originalPropagate_9 & nextResult_originalPropagate_8); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_163 = nextResult_originalPropagate_12 & nextResult_originalPropagate_11 & (
    nextResult_originalPropagate_10 & nextResult_originalPropagate_9); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_164 = nextResult_originalPropagate_13 & nextResult_originalPropagate_12 & (
    nextResult_originalPropagate_11 & nextResult_originalPropagate_10); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_165 = nextResult_originalPropagate_14 & nextResult_originalPropagate_13 & (
    nextResult_originalPropagate_12 & nextResult_originalPropagate_11); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_166 = nextResult_originalPropagate_15 & nextResult_originalPropagate_14 & (
    nextResult_originalPropagate_13 & nextResult_originalPropagate_12); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_167 = nextResult_originalPropagate_16 & nextResult_originalPropagate_15 & (
    nextResult_originalPropagate_14 & nextResult_originalPropagate_13); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_168 = nextResult_originalPropagate_17 & nextResult_originalPropagate_16 & (
    nextResult_originalPropagate_15 & nextResult_originalPropagate_14); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_169 = nextResult_originalPropagate_18 & nextResult_originalPropagate_17 & (
    nextResult_originalPropagate_16 & nextResult_originalPropagate_15); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_170 = nextResult_originalPropagate_19 & nextResult_originalPropagate_18 & (
    nextResult_originalPropagate_17 & nextResult_originalPropagate_16); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_171 = nextResult_originalPropagate_20 & nextResult_originalPropagate_19 & (
    nextResult_originalPropagate_18 & nextResult_originalPropagate_17); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_172 = nextResult_originalPropagate_21 & nextResult_originalPropagate_20 & (
    nextResult_originalPropagate_19 & nextResult_originalPropagate_18); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_173 = nextResult_originalPropagate_22 & nextResult_originalPropagate_21 & (
    nextResult_originalPropagate_20 & nextResult_originalPropagate_19); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_174 = nextResult_originalPropagate_23 & nextResult_originalPropagate_22 & (
    nextResult_originalPropagate_21 & nextResult_originalPropagate_20); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_175 = nextResult_originalPropagate_24 & nextResult_originalPropagate_23 & (
    nextResult_originalPropagate_22 & nextResult_originalPropagate_21); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_176 = nextResult_originalPropagate_25 & nextResult_originalPropagate_24 & (
    nextResult_originalPropagate_23 & nextResult_originalPropagate_22); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_177 = nextResult_originalPropagate_26 & nextResult_originalPropagate_25 & (
    nextResult_originalPropagate_24 & nextResult_originalPropagate_23); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_178 = nextResult_originalPropagate_27 & nextResult_originalPropagate_26 & (
    nextResult_originalPropagate_25 & nextResult_originalPropagate_24); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_179 = nextResult_originalPropagate_28 & nextResult_originalPropagate_27 & (
    nextResult_originalPropagate_26 & nextResult_originalPropagate_25); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_180 = nextResult_originalPropagate_29 & nextResult_originalPropagate_28 & (
    nextResult_originalPropagate_27 & nextResult_originalPropagate_26); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_181 = nextResult_originalPropagate_30 & nextResult_originalPropagate_29 & (
    nextResult_originalPropagate_28 & nextResult_originalPropagate_27); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_184 = nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3 |
    _nextResult_T_65 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1) |
    _nextResult_T_155 & nextResult_generate_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_186 = nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4 |
    _nextResult_T_66 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2) |
    _nextResult_T_156 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_188 = nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5 |
    _nextResult_T_67 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3) |
    _nextResult_T_157 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1 |
    _nextResult_T_63 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_190 = nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6 |
    _nextResult_T_68 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4) |
    _nextResult_T_158 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2 |
    _nextResult_T_64 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_243 = nextResult_originalPropagate_8 & nextResult_originalPropagate_7 & (
    nextResult_originalPropagate_6 & nextResult_originalPropagate_5) & (nextResult_originalPropagate_4 &
    nextResult_originalPropagate_3 & (nextResult_originalPropagate_2 & nextResult_originalPropagate_1)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_244 = nextResult_originalPropagate_9 & nextResult_originalPropagate_8 & (
    nextResult_originalPropagate_7 & nextResult_originalPropagate_6) & (nextResult_originalPropagate_5 &
    nextResult_originalPropagate_4 & (nextResult_originalPropagate_3 & nextResult_originalPropagate_2)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_245 = nextResult_originalPropagate_10 & nextResult_originalPropagate_9 & (
    nextResult_originalPropagate_8 & nextResult_originalPropagate_7) & (nextResult_originalPropagate_6 &
    nextResult_originalPropagate_5 & (nextResult_originalPropagate_4 & nextResult_originalPropagate_3)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_246 = nextResult_originalPropagate_11 & nextResult_originalPropagate_10 & (
    nextResult_originalPropagate_9 & nextResult_originalPropagate_8) & (nextResult_originalPropagate_7 &
    nextResult_originalPropagate_6 & (nextResult_originalPropagate_5 & nextResult_originalPropagate_4)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_247 = nextResult_originalPropagate_12 & nextResult_originalPropagate_11 & (
    nextResult_originalPropagate_10 & nextResult_originalPropagate_9) & (nextResult_originalPropagate_8 &
    nextResult_originalPropagate_7 & (nextResult_originalPropagate_6 & nextResult_originalPropagate_5)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_248 = nextResult_originalPropagate_13 & nextResult_originalPropagate_12 & (
    nextResult_originalPropagate_11 & nextResult_originalPropagate_10) & (nextResult_originalPropagate_9 &
    nextResult_originalPropagate_8 & (nextResult_originalPropagate_7 & nextResult_originalPropagate_6)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_249 = nextResult_originalPropagate_14 & nextResult_originalPropagate_13 & (
    nextResult_originalPropagate_12 & nextResult_originalPropagate_11) & (nextResult_originalPropagate_10 &
    nextResult_originalPropagate_9 & (nextResult_originalPropagate_8 & nextResult_originalPropagate_7)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_250 = nextResult_originalPropagate_15 & nextResult_originalPropagate_14 & (
    nextResult_originalPropagate_13 & nextResult_originalPropagate_12) & (nextResult_originalPropagate_11 &
    nextResult_originalPropagate_10 & (nextResult_originalPropagate_9 & nextResult_originalPropagate_8)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_251 = nextResult_originalPropagate_16 & nextResult_originalPropagate_15 & (
    nextResult_originalPropagate_14 & nextResult_originalPropagate_13) & (nextResult_originalPropagate_12 &
    nextResult_originalPropagate_11 & (nextResult_originalPropagate_10 & nextResult_originalPropagate_9)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_252 = nextResult_originalPropagate_17 & nextResult_originalPropagate_16 & (
    nextResult_originalPropagate_15 & nextResult_originalPropagate_14) & (nextResult_originalPropagate_13 &
    nextResult_originalPropagate_12 & (nextResult_originalPropagate_11 & nextResult_originalPropagate_10)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_253 = nextResult_originalPropagate_18 & nextResult_originalPropagate_17 & (
    nextResult_originalPropagate_16 & nextResult_originalPropagate_15) & (nextResult_originalPropagate_14 &
    nextResult_originalPropagate_13 & (nextResult_originalPropagate_12 & nextResult_originalPropagate_11)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_254 = nextResult_originalPropagate_19 & nextResult_originalPropagate_18 & (
    nextResult_originalPropagate_17 & nextResult_originalPropagate_16) & (nextResult_originalPropagate_15 &
    nextResult_originalPropagate_14 & (nextResult_originalPropagate_13 & nextResult_originalPropagate_12)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_255 = nextResult_originalPropagate_20 & nextResult_originalPropagate_19 & (
    nextResult_originalPropagate_18 & nextResult_originalPropagate_17) & (nextResult_originalPropagate_16 &
    nextResult_originalPropagate_15 & (nextResult_originalPropagate_14 & nextResult_originalPropagate_13)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_256 = nextResult_originalPropagate_21 & nextResult_originalPropagate_20 & (
    nextResult_originalPropagate_19 & nextResult_originalPropagate_18) & (nextResult_originalPropagate_17 &
    nextResult_originalPropagate_16 & (nextResult_originalPropagate_15 & nextResult_originalPropagate_14)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_257 = nextResult_originalPropagate_22 & nextResult_originalPropagate_21 & (
    nextResult_originalPropagate_20 & nextResult_originalPropagate_19) & (nextResult_originalPropagate_18 &
    nextResult_originalPropagate_17 & (nextResult_originalPropagate_16 & nextResult_originalPropagate_15)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_258 = nextResult_originalPropagate_23 & nextResult_originalPropagate_22 & (
    nextResult_originalPropagate_21 & nextResult_originalPropagate_20) & (nextResult_originalPropagate_19 &
    nextResult_originalPropagate_18 & (nextResult_originalPropagate_17 & nextResult_originalPropagate_16)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_259 = nextResult_originalPropagate_24 & nextResult_originalPropagate_23 & (
    nextResult_originalPropagate_22 & nextResult_originalPropagate_21) & (nextResult_originalPropagate_20 &
    nextResult_originalPropagate_19 & (nextResult_originalPropagate_18 & nextResult_originalPropagate_17)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_260 = nextResult_originalPropagate_25 & nextResult_originalPropagate_24 & (
    nextResult_originalPropagate_23 & nextResult_originalPropagate_22) & (nextResult_originalPropagate_21 &
    nextResult_originalPropagate_20 & (nextResult_originalPropagate_19 & nextResult_originalPropagate_18)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_261 = nextResult_originalPropagate_26 & nextResult_originalPropagate_25 & (
    nextResult_originalPropagate_24 & nextResult_originalPropagate_23) & (nextResult_originalPropagate_22 &
    nextResult_originalPropagate_21 & (nextResult_originalPropagate_20 & nextResult_originalPropagate_19)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_262 = nextResult_originalPropagate_27 & nextResult_originalPropagate_26 & (
    nextResult_originalPropagate_25 & nextResult_originalPropagate_24) & (nextResult_originalPropagate_23 &
    nextResult_originalPropagate_22 & (nextResult_originalPropagate_21 & nextResult_originalPropagate_20)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_263 = nextResult_originalPropagate_28 & nextResult_originalPropagate_27 & (
    nextResult_originalPropagate_26 & nextResult_originalPropagate_25) & (nextResult_originalPropagate_24 &
    nextResult_originalPropagate_23 & (nextResult_originalPropagate_22 & nextResult_originalPropagate_21)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_264 = nextResult_originalPropagate_29 & nextResult_originalPropagate_28 & (
    nextResult_originalPropagate_27 & nextResult_originalPropagate_26) & (nextResult_originalPropagate_25 &
    nextResult_originalPropagate_24 & (nextResult_originalPropagate_23 & nextResult_originalPropagate_22)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_265 = nextResult_originalPropagate_30 & nextResult_originalPropagate_29 & (
    nextResult_originalPropagate_28 & nextResult_originalPropagate_27) & (nextResult_originalPropagate_26 &
    nextResult_originalPropagate_25 & (nextResult_originalPropagate_24 & nextResult_originalPropagate_23)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_268 = nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7 |
    _nextResult_T_69 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5) |
    _nextResult_T_159 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3 |
    _nextResult_T_65 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1)) |
    _nextResult_T_243 & nextResult_generate_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_270 = nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8 |
    _nextResult_T_70 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6) |
    _nextResult_T_160 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4 |
    _nextResult_T_66 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2)) |
    _nextResult_T_244 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_272 = nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9 |
    _nextResult_T_71 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7) |
    _nextResult_T_161 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5 |
    _nextResult_T_67 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3)) |
    _nextResult_T_245 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1 |
    _nextResult_T_63 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_274 = nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10 |
    _nextResult_T_72 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8) |
    _nextResult_T_162 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6 |
    _nextResult_T_68 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4)) |
    _nextResult_T_246 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2 |
    _nextResult_T_64 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_276 = nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11 |
    _nextResult_T_73 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9) |
    _nextResult_T_163 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7 |
    _nextResult_T_69 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5)) |
    _nextResult_T_247 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3 |
    _nextResult_T_65 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1) |
    _nextResult_T_155 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_278 = nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12 |
    _nextResult_T_74 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10) |
    _nextResult_T_164 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8 |
    _nextResult_T_70 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6)) |
    _nextResult_T_248 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4 |
    _nextResult_T_66 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2) |
    _nextResult_T_156 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_280 = nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13 |
    _nextResult_T_75 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11) |
    _nextResult_T_165 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9 |
    _nextResult_T_71 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7)) |
    _nextResult_T_249 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5 |
    _nextResult_T_67 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3) |
    _nextResult_T_157 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1 |
    _nextResult_T_63 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_282 = nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14 |
    _nextResult_T_76 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12) |
    _nextResult_T_166 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10 |
    _nextResult_T_72 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8)) |
    _nextResult_T_250 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6 |
    _nextResult_T_68 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4) |
    _nextResult_T_158 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2 |
    _nextResult_T_64 & (nextResult_generate_1 | nextResult_originalPropagate_1 & nextResult_generate_0))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_284 = nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15 |
    _nextResult_T_77 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13) |
    _nextResult_T_167 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11 |
    _nextResult_T_73 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9)) |
    _nextResult_T_251 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7 |
    _nextResult_T_69 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5) |
    _nextResult_T_159 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3 |
    _nextResult_T_65 & (nextResult_generate_2 | nextResult_originalPropagate_2 & nextResult_generate_1))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_286 = nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16 |
    _nextResult_T_78 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14) |
    _nextResult_T_168 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12 |
    _nextResult_T_74 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10)) |
    _nextResult_T_252 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8 |
    _nextResult_T_70 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6) |
    _nextResult_T_160 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4 |
    _nextResult_T_66 & (nextResult_generate_3 | nextResult_originalPropagate_3 & nextResult_generate_2))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_288 = nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17 |
    _nextResult_T_79 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15) |
    _nextResult_T_169 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13 |
    _nextResult_T_75 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11)) |
    _nextResult_T_253 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9 |
    _nextResult_T_71 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7) |
    _nextResult_T_161 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5 |
    _nextResult_T_67 & (nextResult_generate_4 | nextResult_originalPropagate_4 & nextResult_generate_3))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_290 = nextResult_generate_19 | nextResult_originalPropagate_19 & nextResult_generate_18 |
    _nextResult_T_80 & (nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16) |
    _nextResult_T_170 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14 |
    _nextResult_T_76 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12)) |
    _nextResult_T_254 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10 |
    _nextResult_T_72 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8) |
    _nextResult_T_162 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6 |
    _nextResult_T_68 & (nextResult_generate_5 | nextResult_originalPropagate_5 & nextResult_generate_4))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_292 = nextResult_generate_20 | nextResult_originalPropagate_20 & nextResult_generate_19 |
    _nextResult_T_81 & (nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17) |
    _nextResult_T_171 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15 |
    _nextResult_T_77 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13)) |
    _nextResult_T_255 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11 |
    _nextResult_T_73 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9) |
    _nextResult_T_163 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7 |
    _nextResult_T_69 & (nextResult_generate_6 | nextResult_originalPropagate_6 & nextResult_generate_5))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_294 = nextResult_generate_21 | nextResult_originalPropagate_21 & nextResult_generate_20 |
    _nextResult_T_82 & (nextResult_generate_19 | nextResult_originalPropagate_19 & nextResult_generate_18) |
    _nextResult_T_172 & (nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16 |
    _nextResult_T_78 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14)) |
    _nextResult_T_256 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12 |
    _nextResult_T_74 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10) |
    _nextResult_T_164 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8 |
    _nextResult_T_70 & (nextResult_generate_7 | nextResult_originalPropagate_7 & nextResult_generate_6))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_296 = nextResult_generate_22 | nextResult_originalPropagate_22 & nextResult_generate_21 |
    _nextResult_T_83 & (nextResult_generate_20 | nextResult_originalPropagate_20 & nextResult_generate_19) |
    _nextResult_T_173 & (nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17 |
    _nextResult_T_79 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15)) |
    _nextResult_T_257 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13 |
    _nextResult_T_75 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11) |
    _nextResult_T_165 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9 |
    _nextResult_T_71 & (nextResult_generate_8 | nextResult_originalPropagate_8 & nextResult_generate_7))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_298 = nextResult_generate_23 | nextResult_originalPropagate_23 & nextResult_generate_22 |
    _nextResult_T_84 & (nextResult_generate_21 | nextResult_originalPropagate_21 & nextResult_generate_20) |
    _nextResult_T_174 & (nextResult_generate_19 | nextResult_originalPropagate_19 & nextResult_generate_18 |
    _nextResult_T_80 & (nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16)) |
    _nextResult_T_258 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14 |
    _nextResult_T_76 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12) |
    _nextResult_T_166 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10 |
    _nextResult_T_72 & (nextResult_generate_9 | nextResult_originalPropagate_9 & nextResult_generate_8))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_300 = nextResult_generate_24 | nextResult_originalPropagate_24 & nextResult_generate_23 |
    _nextResult_T_85 & (nextResult_generate_22 | nextResult_originalPropagate_22 & nextResult_generate_21) |
    _nextResult_T_175 & (nextResult_generate_20 | nextResult_originalPropagate_20 & nextResult_generate_19 |
    _nextResult_T_81 & (nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17)) |
    _nextResult_T_259 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15 |
    _nextResult_T_77 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13) |
    _nextResult_T_167 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11 |
    _nextResult_T_73 & (nextResult_generate_10 | nextResult_originalPropagate_10 & nextResult_generate_9))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_302 = nextResult_generate_25 | nextResult_originalPropagate_25 & nextResult_generate_24 |
    _nextResult_T_86 & (nextResult_generate_23 | nextResult_originalPropagate_23 & nextResult_generate_22) |
    _nextResult_T_176 & (nextResult_generate_21 | nextResult_originalPropagate_21 & nextResult_generate_20 |
    _nextResult_T_82 & (nextResult_generate_19 | nextResult_originalPropagate_19 & nextResult_generate_18)) |
    _nextResult_T_260 & (nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16 |
    _nextResult_T_78 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14) |
    _nextResult_T_168 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12 |
    _nextResult_T_74 & (nextResult_generate_11 | nextResult_originalPropagate_11 & nextResult_generate_10))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_304 = nextResult_generate_26 | nextResult_originalPropagate_26 & nextResult_generate_25 |
    _nextResult_T_87 & (nextResult_generate_24 | nextResult_originalPropagate_24 & nextResult_generate_23) |
    _nextResult_T_177 & (nextResult_generate_22 | nextResult_originalPropagate_22 & nextResult_generate_21 |
    _nextResult_T_83 & (nextResult_generate_20 | nextResult_originalPropagate_20 & nextResult_generate_19)) |
    _nextResult_T_261 & (nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17 |
    _nextResult_T_79 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15) |
    _nextResult_T_169 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13 |
    _nextResult_T_75 & (nextResult_generate_12 | nextResult_originalPropagate_12 & nextResult_generate_11))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_306 = nextResult_generate_27 | nextResult_originalPropagate_27 & nextResult_generate_26 |
    _nextResult_T_88 & (nextResult_generate_25 | nextResult_originalPropagate_25 & nextResult_generate_24) |
    _nextResult_T_178 & (nextResult_generate_23 | nextResult_originalPropagate_23 & nextResult_generate_22 |
    _nextResult_T_84 & (nextResult_generate_21 | nextResult_originalPropagate_21 & nextResult_generate_20)) |
    _nextResult_T_262 & (nextResult_generate_19 | nextResult_originalPropagate_19 & nextResult_generate_18 |
    _nextResult_T_80 & (nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16) |
    _nextResult_T_170 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14 |
    _nextResult_T_76 & (nextResult_generate_13 | nextResult_originalPropagate_13 & nextResult_generate_12))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_308 = nextResult_generate_28 | nextResult_originalPropagate_28 & nextResult_generate_27 |
    _nextResult_T_89 & (nextResult_generate_26 | nextResult_originalPropagate_26 & nextResult_generate_25) |
    _nextResult_T_179 & (nextResult_generate_24 | nextResult_originalPropagate_24 & nextResult_generate_23 |
    _nextResult_T_85 & (nextResult_generate_22 | nextResult_originalPropagate_22 & nextResult_generate_21)) |
    _nextResult_T_263 & (nextResult_generate_20 | nextResult_originalPropagate_20 & nextResult_generate_19 |
    _nextResult_T_81 & (nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17) |
    _nextResult_T_171 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15 |
    _nextResult_T_77 & (nextResult_generate_14 | nextResult_originalPropagate_14 & nextResult_generate_13))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_310 = nextResult_generate_29 | nextResult_originalPropagate_29 & nextResult_generate_28 |
    _nextResult_T_90 & (nextResult_generate_27 | nextResult_originalPropagate_27 & nextResult_generate_26) |
    _nextResult_T_180 & (nextResult_generate_25 | nextResult_originalPropagate_25 & nextResult_generate_24 |
    _nextResult_T_86 & (nextResult_generate_23 | nextResult_originalPropagate_23 & nextResult_generate_22)) |
    _nextResult_T_264 & (nextResult_generate_21 | nextResult_originalPropagate_21 & nextResult_generate_20 |
    _nextResult_T_82 & (nextResult_generate_19 | nextResult_originalPropagate_19 & nextResult_generate_18) |
    _nextResult_T_172 & (nextResult_generate_17 | nextResult_originalPropagate_17 & nextResult_generate_16 |
    _nextResult_T_78 & (nextResult_generate_15 | nextResult_originalPropagate_15 & nextResult_generate_14))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_312 = nextResult_generate_30 | nextResult_originalPropagate_30 & nextResult_generate_29 |
    _nextResult_T_91 & (nextResult_generate_28 | nextResult_originalPropagate_28 & nextResult_generate_27) |
    _nextResult_T_181 & (nextResult_generate_26 | nextResult_originalPropagate_26 & nextResult_generate_25 |
    _nextResult_T_87 & (nextResult_generate_24 | nextResult_originalPropagate_24 & nextResult_generate_23)) |
    _nextResult_T_265 & (nextResult_generate_22 | nextResult_originalPropagate_22 & nextResult_generate_21 |
    _nextResult_T_83 & (nextResult_generate_20 | nextResult_originalPropagate_20 & nextResult_generate_19) |
    _nextResult_T_173 & (nextResult_generate_18 | nextResult_originalPropagate_18 & nextResult_generate_17 |
    _nextResult_T_79 & (nextResult_generate_16 | nextResult_originalPropagate_16 & nextResult_generate_15))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_323 = nextResult_originalPropagate_16 & nextResult_originalPropagate_15 & (
    nextResult_originalPropagate_14 & nextResult_originalPropagate_13) & (nextResult_originalPropagate_12 &
    nextResult_originalPropagate_11 & (nextResult_originalPropagate_10 & nextResult_originalPropagate_9)) & (
    nextResult_originalPropagate_8 & nextResult_originalPropagate_7 & (nextResult_originalPropagate_6 &
    nextResult_originalPropagate_5) & (nextResult_originalPropagate_4 & nextResult_originalPropagate_3 & (
    nextResult_originalPropagate_2 & nextResult_originalPropagate_1))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_324 = nextResult_originalPropagate_17 & nextResult_originalPropagate_16 & (
    nextResult_originalPropagate_15 & nextResult_originalPropagate_14) & (nextResult_originalPropagate_13 &
    nextResult_originalPropagate_12 & (nextResult_originalPropagate_11 & nextResult_originalPropagate_10)) & (
    nextResult_originalPropagate_9 & nextResult_originalPropagate_8 & (nextResult_originalPropagate_7 &
    nextResult_originalPropagate_6) & (nextResult_originalPropagate_5 & nextResult_originalPropagate_4 & (
    nextResult_originalPropagate_3 & nextResult_originalPropagate_2))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_325 = nextResult_originalPropagate_18 & nextResult_originalPropagate_17 & (
    nextResult_originalPropagate_16 & nextResult_originalPropagate_15) & (nextResult_originalPropagate_14 &
    nextResult_originalPropagate_13 & (nextResult_originalPropagate_12 & nextResult_originalPropagate_11)) & (
    nextResult_originalPropagate_10 & nextResult_originalPropagate_9 & (nextResult_originalPropagate_8 &
    nextResult_originalPropagate_7) & (nextResult_originalPropagate_6 & nextResult_originalPropagate_5 & (
    nextResult_originalPropagate_4 & nextResult_originalPropagate_3))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_326 = nextResult_originalPropagate_19 & nextResult_originalPropagate_18 & (
    nextResult_originalPropagate_17 & nextResult_originalPropagate_16) & (nextResult_originalPropagate_15 &
    nextResult_originalPropagate_14 & (nextResult_originalPropagate_13 & nextResult_originalPropagate_12)) & (
    nextResult_originalPropagate_11 & nextResult_originalPropagate_10 & (nextResult_originalPropagate_9 &
    nextResult_originalPropagate_8) & (nextResult_originalPropagate_7 & nextResult_originalPropagate_6 & (
    nextResult_originalPropagate_5 & nextResult_originalPropagate_4))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_327 = nextResult_originalPropagate_20 & nextResult_originalPropagate_19 & (
    nextResult_originalPropagate_18 & nextResult_originalPropagate_17) & (nextResult_originalPropagate_16 &
    nextResult_originalPropagate_15 & (nextResult_originalPropagate_14 & nextResult_originalPropagate_13)) & (
    nextResult_originalPropagate_12 & nextResult_originalPropagate_11 & (nextResult_originalPropagate_10 &
    nextResult_originalPropagate_9) & (nextResult_originalPropagate_8 & nextResult_originalPropagate_7 & (
    nextResult_originalPropagate_6 & nextResult_originalPropagate_5))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_328 = nextResult_originalPropagate_21 & nextResult_originalPropagate_20 & (
    nextResult_originalPropagate_19 & nextResult_originalPropagate_18) & (nextResult_originalPropagate_17 &
    nextResult_originalPropagate_16 & (nextResult_originalPropagate_15 & nextResult_originalPropagate_14)) & (
    nextResult_originalPropagate_13 & nextResult_originalPropagate_12 & (nextResult_originalPropagate_11 &
    nextResult_originalPropagate_10) & (nextResult_originalPropagate_9 & nextResult_originalPropagate_8 & (
    nextResult_originalPropagate_7 & nextResult_originalPropagate_6))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_329 = nextResult_originalPropagate_22 & nextResult_originalPropagate_21 & (
    nextResult_originalPropagate_20 & nextResult_originalPropagate_19) & (nextResult_originalPropagate_18 &
    nextResult_originalPropagate_17 & (nextResult_originalPropagate_16 & nextResult_originalPropagate_15)) & (
    nextResult_originalPropagate_14 & nextResult_originalPropagate_13 & (nextResult_originalPropagate_12 &
    nextResult_originalPropagate_11) & (nextResult_originalPropagate_10 & nextResult_originalPropagate_9 & (
    nextResult_originalPropagate_8 & nextResult_originalPropagate_7))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_330 = nextResult_originalPropagate_23 & nextResult_originalPropagate_22 & (
    nextResult_originalPropagate_21 & nextResult_originalPropagate_20) & (nextResult_originalPropagate_19 &
    nextResult_originalPropagate_18 & (nextResult_originalPropagate_17 & nextResult_originalPropagate_16)) & (
    nextResult_originalPropagate_15 & nextResult_originalPropagate_14 & (nextResult_originalPropagate_13 &
    nextResult_originalPropagate_12) & (nextResult_originalPropagate_11 & nextResult_originalPropagate_10 & (
    nextResult_originalPropagate_9 & nextResult_originalPropagate_8))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_331 = nextResult_originalPropagate_24 & nextResult_originalPropagate_23 & (
    nextResult_originalPropagate_22 & nextResult_originalPropagate_21) & (nextResult_originalPropagate_20 &
    nextResult_originalPropagate_19 & (nextResult_originalPropagate_18 & nextResult_originalPropagate_17)) & (
    nextResult_originalPropagate_16 & nextResult_originalPropagate_15 & (nextResult_originalPropagate_14 &
    nextResult_originalPropagate_13) & (nextResult_originalPropagate_12 & nextResult_originalPropagate_11 & (
    nextResult_originalPropagate_10 & nextResult_originalPropagate_9))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_332 = nextResult_originalPropagate_25 & nextResult_originalPropagate_24 & (
    nextResult_originalPropagate_23 & nextResult_originalPropagate_22) & (nextResult_originalPropagate_21 &
    nextResult_originalPropagate_20 & (nextResult_originalPropagate_19 & nextResult_originalPropagate_18)) & (
    nextResult_originalPropagate_17 & nextResult_originalPropagate_16 & (nextResult_originalPropagate_15 &
    nextResult_originalPropagate_14) & (nextResult_originalPropagate_13 & nextResult_originalPropagate_12 & (
    nextResult_originalPropagate_11 & nextResult_originalPropagate_10))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_333 = nextResult_originalPropagate_26 & nextResult_originalPropagate_25 & (
    nextResult_originalPropagate_24 & nextResult_originalPropagate_23) & (nextResult_originalPropagate_22 &
    nextResult_originalPropagate_21 & (nextResult_originalPropagate_20 & nextResult_originalPropagate_19)) & (
    nextResult_originalPropagate_18 & nextResult_originalPropagate_17 & (nextResult_originalPropagate_16 &
    nextResult_originalPropagate_15) & (nextResult_originalPropagate_14 & nextResult_originalPropagate_13 & (
    nextResult_originalPropagate_12 & nextResult_originalPropagate_11))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_334 = nextResult_originalPropagate_27 & nextResult_originalPropagate_26 & (
    nextResult_originalPropagate_25 & nextResult_originalPropagate_24) & (nextResult_originalPropagate_23 &
    nextResult_originalPropagate_22 & (nextResult_originalPropagate_21 & nextResult_originalPropagate_20)) & (
    nextResult_originalPropagate_19 & nextResult_originalPropagate_18 & (nextResult_originalPropagate_17 &
    nextResult_originalPropagate_16) & (nextResult_originalPropagate_15 & nextResult_originalPropagate_14 & (
    nextResult_originalPropagate_13 & nextResult_originalPropagate_12))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_335 = nextResult_originalPropagate_28 & nextResult_originalPropagate_27 & (
    nextResult_originalPropagate_26 & nextResult_originalPropagate_25) & (nextResult_originalPropagate_24 &
    nextResult_originalPropagate_23 & (nextResult_originalPropagate_22 & nextResult_originalPropagate_21)) & (
    nextResult_originalPropagate_20 & nextResult_originalPropagate_19 & (nextResult_originalPropagate_18 &
    nextResult_originalPropagate_17) & (nextResult_originalPropagate_16 & nextResult_originalPropagate_15 & (
    nextResult_originalPropagate_14 & nextResult_originalPropagate_13))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_336 = nextResult_originalPropagate_29 & nextResult_originalPropagate_28 & (
    nextResult_originalPropagate_27 & nextResult_originalPropagate_26) & (nextResult_originalPropagate_25 &
    nextResult_originalPropagate_24 & (nextResult_originalPropagate_23 & nextResult_originalPropagate_22)) & (
    nextResult_originalPropagate_21 & nextResult_originalPropagate_20 & (nextResult_originalPropagate_19 &
    nextResult_originalPropagate_18) & (nextResult_originalPropagate_17 & nextResult_originalPropagate_16 & (
    nextResult_originalPropagate_15 & nextResult_originalPropagate_14))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_337 = nextResult_originalPropagate_30 & nextResult_originalPropagate_29 & (
    nextResult_originalPropagate_28 & nextResult_originalPropagate_27) & (nextResult_originalPropagate_26 &
    nextResult_originalPropagate_25 & (nextResult_originalPropagate_24 & nextResult_originalPropagate_23)) & (
    nextResult_originalPropagate_22 & nextResult_originalPropagate_21 & (nextResult_originalPropagate_20 &
    nextResult_originalPropagate_19) & (nextResult_originalPropagate_18 & nextResult_originalPropagate_17 & (
    nextResult_originalPropagate_16 & nextResult_originalPropagate_15))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 86:30]
  wire  _nextResult_T_340 = _nextResult_T_284 | _nextResult_T_323 & nextResult_generate_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_342 = _nextResult_T_286 | _nextResult_T_324 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_344 = _nextResult_T_288 | _nextResult_T_325 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1 | _nextResult_T_63 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_346 = _nextResult_T_290 | _nextResult_T_326 & (nextResult_generate_3 |
    nextResult_originalPropagate_3 & nextResult_generate_2 | _nextResult_T_64 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_348 = _nextResult_T_292 | _nextResult_T_327 & (nextResult_generate_4 |
    nextResult_originalPropagate_4 & nextResult_generate_3 | _nextResult_T_65 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1) | _nextResult_T_155 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_350 = _nextResult_T_294 | _nextResult_T_328 & (nextResult_generate_5 |
    nextResult_originalPropagate_5 & nextResult_generate_4 | _nextResult_T_66 & (nextResult_generate_3 |
    nextResult_originalPropagate_3 & nextResult_generate_2) | _nextResult_T_156 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_352 = _nextResult_T_296 | _nextResult_T_329 & (nextResult_generate_6 |
    nextResult_originalPropagate_6 & nextResult_generate_5 | _nextResult_T_67 & (nextResult_generate_4 |
    nextResult_originalPropagate_4 & nextResult_generate_3) | _nextResult_T_157 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1 | _nextResult_T_63 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_354 = _nextResult_T_298 | _nextResult_T_330 & (nextResult_generate_7 |
    nextResult_originalPropagate_7 & nextResult_generate_6 | _nextResult_T_68 & (nextResult_generate_5 |
    nextResult_originalPropagate_5 & nextResult_generate_4) | _nextResult_T_158 & (nextResult_generate_3 |
    nextResult_originalPropagate_3 & nextResult_generate_2 | _nextResult_T_64 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_356 = _nextResult_T_300 | _nextResult_T_331 & (nextResult_generate_8 |
    nextResult_originalPropagate_8 & nextResult_generate_7 | _nextResult_T_69 & (nextResult_generate_6 |
    nextResult_originalPropagate_6 & nextResult_generate_5) | _nextResult_T_159 & (nextResult_generate_4 |
    nextResult_originalPropagate_4 & nextResult_generate_3 | _nextResult_T_65 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1)) | _nextResult_T_243 & nextResult_generate_0); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_358 = _nextResult_T_302 | _nextResult_T_332 & (nextResult_generate_9 |
    nextResult_originalPropagate_9 & nextResult_generate_8 | _nextResult_T_70 & (nextResult_generate_7 |
    nextResult_originalPropagate_7 & nextResult_generate_6) | _nextResult_T_160 & (nextResult_generate_5 |
    nextResult_originalPropagate_5 & nextResult_generate_4 | _nextResult_T_66 & (nextResult_generate_3 |
    nextResult_originalPropagate_3 & nextResult_generate_2)) | _nextResult_T_244 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_360 = _nextResult_T_304 | _nextResult_T_333 & (nextResult_generate_10 |
    nextResult_originalPropagate_10 & nextResult_generate_9 | _nextResult_T_71 & (nextResult_generate_8 |
    nextResult_originalPropagate_8 & nextResult_generate_7) | _nextResult_T_161 & (nextResult_generate_6 |
    nextResult_originalPropagate_6 & nextResult_generate_5 | _nextResult_T_67 & (nextResult_generate_4 |
    nextResult_originalPropagate_4 & nextResult_generate_3)) | _nextResult_T_245 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1 | _nextResult_T_63 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_362 = _nextResult_T_306 | _nextResult_T_334 & (nextResult_generate_11 |
    nextResult_originalPropagate_11 & nextResult_generate_10 | _nextResult_T_72 & (nextResult_generate_9 |
    nextResult_originalPropagate_9 & nextResult_generate_8) | _nextResult_T_162 & (nextResult_generate_7 |
    nextResult_originalPropagate_7 & nextResult_generate_6 | _nextResult_T_68 & (nextResult_generate_5 |
    nextResult_originalPropagate_5 & nextResult_generate_4)) | _nextResult_T_246 & (nextResult_generate_3 |
    nextResult_originalPropagate_3 & nextResult_generate_2 | _nextResult_T_64 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_364 = _nextResult_T_308 | _nextResult_T_335 & (nextResult_generate_12 |
    nextResult_originalPropagate_12 & nextResult_generate_11 | _nextResult_T_73 & (nextResult_generate_10 |
    nextResult_originalPropagate_10 & nextResult_generate_9) | _nextResult_T_163 & (nextResult_generate_8 |
    nextResult_originalPropagate_8 & nextResult_generate_7 | _nextResult_T_69 & (nextResult_generate_6 |
    nextResult_originalPropagate_6 & nextResult_generate_5)) | _nextResult_T_247 & (nextResult_generate_4 |
    nextResult_originalPropagate_4 & nextResult_generate_3 | _nextResult_T_65 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1) | _nextResult_T_155 & nextResult_generate_0)); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_366 = _nextResult_T_310 | _nextResult_T_336 & (nextResult_generate_13 |
    nextResult_originalPropagate_13 & nextResult_generate_12 | _nextResult_T_74 & (nextResult_generate_11 |
    nextResult_originalPropagate_11 & nextResult_generate_10) | _nextResult_T_164 & (nextResult_generate_9 |
    nextResult_originalPropagate_9 & nextResult_generate_8 | _nextResult_T_70 & (nextResult_generate_7 |
    nextResult_originalPropagate_7 & nextResult_generate_6)) | _nextResult_T_248 & (nextResult_generate_5 |
    nextResult_originalPropagate_5 & nextResult_generate_4 | _nextResult_T_66 & (nextResult_generate_3 |
    nextResult_originalPropagate_3 & nextResult_generate_2) | _nextResult_T_156 & (nextResult_generate_1 |
    nextResult_originalPropagate_1 & nextResult_generate_0))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_368 = _nextResult_T_312 | _nextResult_T_337 & (nextResult_generate_14 |
    nextResult_originalPropagate_14 & nextResult_generate_13 | _nextResult_T_75 & (nextResult_generate_12 |
    nextResult_originalPropagate_12 & nextResult_generate_11) | _nextResult_T_165 & (nextResult_generate_10 |
    nextResult_originalPropagate_10 & nextResult_generate_9 | _nextResult_T_71 & (nextResult_generate_8 |
    nextResult_originalPropagate_8 & nextResult_generate_7)) | _nextResult_T_249 & (nextResult_generate_6 |
    nextResult_originalPropagate_6 & nextResult_generate_5 | _nextResult_T_67 & (nextResult_generate_4 |
    nextResult_originalPropagate_4 & nextResult_generate_3) | _nextResult_T_157 & (nextResult_generate_2 |
    nextResult_originalPropagate_2 & nextResult_generate_1 | _nextResult_T_63 & nextResult_generate_0))); // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 84:29]
  wire  _nextResult_T_388 = nextResult_originalPropagate_1 ^ nextResult_generate_0; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_389 = nextResult_originalPropagate_2 ^ _nextResult_T_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_390 = nextResult_originalPropagate_3 ^ _nextResult_T_94; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_391 = nextResult_originalPropagate_4 ^ _nextResult_T_96; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_392 = nextResult_originalPropagate_5 ^ _nextResult_T_184; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_393 = nextResult_originalPropagate_6 ^ _nextResult_T_186; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_394 = nextResult_originalPropagate_7 ^ _nextResult_T_188; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_395 = nextResult_originalPropagate_8 ^ _nextResult_T_190; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_396 = nextResult_originalPropagate_9 ^ _nextResult_T_268; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_397 = nextResult_originalPropagate_10 ^ _nextResult_T_270; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_398 = nextResult_originalPropagate_11 ^ _nextResult_T_272; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_399 = nextResult_originalPropagate_12 ^ _nextResult_T_274; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_400 = nextResult_originalPropagate_13 ^ _nextResult_T_276; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_401 = nextResult_originalPropagate_14 ^ _nextResult_T_278; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_402 = nextResult_originalPropagate_15 ^ _nextResult_T_280; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_403 = nextResult_originalPropagate_16 ^ _nextResult_T_282; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_404 = nextResult_originalPropagate_17 ^ _nextResult_T_340; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_405 = nextResult_originalPropagate_18 ^ _nextResult_T_342; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_406 = nextResult_originalPropagate_19 ^ _nextResult_T_344; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_407 = nextResult_originalPropagate_20 ^ _nextResult_T_346; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_408 = nextResult_originalPropagate_21 ^ _nextResult_T_348; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_409 = nextResult_originalPropagate_22 ^ _nextResult_T_350; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_410 = nextResult_originalPropagate_23 ^ _nextResult_T_352; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_411 = nextResult_originalPropagate_24 ^ _nextResult_T_354; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_412 = nextResult_originalPropagate_25 ^ _nextResult_T_356; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_413 = nextResult_originalPropagate_26 ^ _nextResult_T_358; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_414 = nextResult_originalPropagate_27 ^ _nextResult_T_360; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_415 = nextResult_originalPropagate_28 ^ _nextResult_T_362; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_416 = nextResult_originalPropagate_29 ^ _nextResult_T_364; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_417 = nextResult_originalPropagate_30 ^ _nextResult_T_366; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire  _nextResult_T_418 = nextResult_originalPropagate_31 ^ _nextResult_T_368; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 88:56]
  wire [7:0] nextResult_lo_lo = {_nextResult_T_394,_nextResult_T_393,_nextResult_T_392,_nextResult_T_391,
    _nextResult_T_390,_nextResult_T_389,_nextResult_T_388,nextResult_originalPropagate_0}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 89:50]
  wire [15:0] nextResult_lo = {_nextResult_T_402,_nextResult_T_401,_nextResult_T_400,_nextResult_T_399,_nextResult_T_398
    ,_nextResult_T_397,_nextResult_T_396,_nextResult_T_395,nextResult_lo_lo}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 89:50]
  wire [7:0] nextResult_hi_lo = {_nextResult_T_410,_nextResult_T_409,_nextResult_T_408,_nextResult_T_407,
    _nextResult_T_406,_nextResult_T_405,_nextResult_T_404,_nextResult_T_403}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 89:50]
  wire [31:0] nextResult = {_nextResult_T_418,_nextResult_T_417,_nextResult_T_416,_nextResult_T_415,_nextResult_T_414,
    _nextResult_T_413,_nextResult_T_412,_nextResult_T_411,nextResult_hi_lo,nextResult_lo}; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 89:50]
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
