module PpaTop(input clock,input enable,input [127:0] vs1,input [127:0] vs2,input [31:0] acc,output [127:0] result);
VdotAccRetimedDatapath dut(.clock(clock),.io_enable1(enable),.io_enable2(enable),.io_vs1(vs1),.io_vs2(vs2),.io_acc(acc),.io_result(result));
endmodule
