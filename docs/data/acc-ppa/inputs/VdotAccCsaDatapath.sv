module VdotAccCsaDatapath( // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 47:7]
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
  wire [31:0] nextResult = nextResult_terms_0 + nextResult_terms_1; // @[third_party/XiangShan/src/main/scala/xiangshan/backend/fu/vector/Vdot.scala 105:66]
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
