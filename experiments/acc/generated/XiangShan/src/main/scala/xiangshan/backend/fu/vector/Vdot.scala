// SPDX-License-Identifier: MulanPSL-2.0
package xiangshan.backend.fu.vector

import chisel3._
import chisel3.util._

/** Provisional CIE-2026 contract, kept outside YunSuan's standard op namespace. */
object VdotEncoding {
  // custom-0, funct6=0, funct3=0; bit25 retains RVV's vm meaning.
  val instruction = BitPat("b000000???????????000?????0001011")
  def op = "b100000000".U(9.W)
  val accumulateInstruction = BitPat("b000001???????????000?????0001011")
  def accOp = "b100000001".U(9.W)
}

/** Two stages, enabled by the existing vector FU pipeline's stage enables.
  * Control validity, ROB flushing and destination tags remain in VecPipedFuncUnit.
  */
class VdotDatapath extends Module {
  val io = IO(new Bundle {
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val enable1 = Input(Bool())
    val enable2 = Input(Bool())
    val result = Output(UInt(128.W))
  })
  val products = Reg(Vec(8, SInt(16.W)))
  when(io.enable1) {
    for (i <- 0 until 8) {
      products(i) := io.vs1(8*i+7, 8*i).asSInt * io.vs2(8*i+7, 8*i).asSInt
    }
  }
  val pairs = (0 until 4).map(i => products(2*i) +& products(2*i+1))
  val quads = (0 until 2).map(i => pairs(2*i) +& pairs(2*i+1))
  val sum = quads(0) +& quads(1) // 19-bit signed, including +131072
  val result = Reg(UInt(128.W))
  when(io.enable2) {
    result := Cat(0.U(96.W), sum.pad(32).asUInt)
  }
  io.result := result
}

/** Experimental fused accumulator. Both operations share the eight multipliers.
  * The caller supplies zero for vdot, or old vd[31:0] for vdot.acc.
  * Addition wraps modulo 2^32; the upper 96 result bits are always zero.
  */
class VdotAccDatapath(useCarrySave: Boolean = true, usePrefix: Boolean = false,
                      retimeFirstCompression: Boolean = false) extends Module {
  require(!retimeFirstCompression || (useCarrySave && usePrefix))
  override def desiredName: String = if (retimeFirstCompression) "VdotAccRetimedDatapath" else if (usePrefix) "VdotAccCsaPrefixDatapath" else if (useCarrySave) "VdotAccCsaDatapath" else "VdotAccPlainDatapath"
  val io = IO(new Bundle {
    val vs1 = Input(UInt(128.W))
    val vs2 = Input(UInt(128.W))
    val acc = Input(UInt(32.W))
    val enable1 = Input(Bool())
    val enable2 = Input(Bool())
    val result = Output(UInt(128.W))
  })
  val inputProducts = Wire(Vec(8, SInt(16.W)))
  for (i <- 0 until 8) {
    inputProducts(i) := io.vs1(8*i+7, 8*i).asSInt * io.vs2(8*i+7, 8*i).asSInt
  }
  private def compressLayer(terms: Seq[UInt]): Seq[UInt] = {
      terms.grouped(3).flatMap { group =>
        if (group.size < 3) group
        else {
          val a = group(0); val b = group(1); val c = group(2)
          val majority = (a & b) | (a & c) | (b & c)
          Seq(a ^ b ^ c, (majority << 1)(31, 0))
        }
      }.toSeq
  }
  private def compress(terms: Seq[UInt]): Seq[UInt] = {
    if (terms.size <= 2) terms else compress(compressLayer(terms))
  }
  private def prefixAdd(a: UInt, b: UInt): UInt = {
    val originalPropagate = (a ^ b).asBools.toSeq
    var generate = (a & b).asBools.toSeq
    var propagate = originalPropagate
    for (distance <- Seq(1, 2, 4, 8, 16)) {
      val oldGenerate = generate
      val oldPropagate = propagate
      generate = (0 until 32).map(i => if (i < distance) oldGenerate(i)
        else oldGenerate(i) || (oldPropagate(i) && oldGenerate(i-distance)))
      propagate = (0 until 32).map(i => if (i < distance) oldPropagate(i)
        else oldPropagate(i) && oldPropagate(i-distance))
    }
    VecInit((0 until 32).map(i => originalPropagate(i) ^
      (if (i == 0) false.B else generate(i-1)))).asUInt
  }
  val nextResult = if (retimeFirstCompression) {
    // Move one compressor layer before the first register boundary. Multipliers
    // remain shared by dot and dot.acc; two enabled edges and II=1 are retained.
    val earlyTerms = compressLayer(inputProducts.toSeq.map(_.pad(32).asUInt) :+ io.acc)
    val level1 = Reg(Vec(earlyTerms.size, UInt(32.W)))
    when(io.enable1) { level1 := VecInit(earlyTerms) }
    val terms = compress(level1.toSeq)
    prefixAdd(terms(0), terms(1))
  } else {
    val products = Reg(Vec(8, SInt(16.W)))
    val accumulator = Reg(UInt(32.W))
    when(io.enable1) { products := inputProducts; accumulator := io.acc }
    if (useCarrySave) {
      val terms = compress(products.toSeq.map(_.pad(32).asUInt) :+ accumulator)
      if (usePrefix) prefixAdd(terms(0), terms(1)) else terms(0) + terms(1)
    } else {
      val pairs = (0 until 4).map(i => products(2*i) +& products(2*i+1))
      val quads = (0 until 2).map(i => pairs(2*i) +& pairs(2*i+1))
      val sum = quads(0) +& quads(1)
      sum.pad(32).asUInt + accumulator
    }
  }
  val result = Reg(UInt(32.W))
  when(io.enable2) { result := nextResult }
  io.result := Cat(0.U(96.W), result)
}
