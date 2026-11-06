import chisel3._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec
import xiangshan.backend.fu.vector.VdotAccDatapath

class VdotAccDatapathTest extends AnyFlatSpec with ChiselScalatestTester {
  behavior of "VdotAccDatapath"
  private val mask32 = (BigInt(1) << 32) - 1
  private def repeated(x: Int): BigInt = (0 until 16).map(i => BigInt(x & 255) << (8*i)).sum
  private def oracle(a: BigInt, b: BigInt, acc: BigInt): BigInt = {
    def signedByte(x: BigInt, i: Int): Int = {
      val byte = ((x >> (8*i)) & 255).toInt
      if (byte < 128) byte else byte - 256
    }
    (acc + (0 until 8).map(i => signedByte(a,i) * signedByte(b,i)).sum) & mask32
  }
  for ((carrySave,prefix,retime) <- Seq((false,false,false), (true,false,false), (true,true,false), (true,true,true))) {
    it should s"preserve modulo arithmetic and independent enables, carrySave=$carrySave prefix=$prefix retime=$retime" in {
      test(new VdotAccDatapath(carrySave,prefix,retime)).withAnnotations(Seq(VerilatorBackendAnnotation)) { dut =>
        val rng = new scala.util.Random(20261106L)
        val directed = Seq((1,1,BigInt(0)),(-1,1,BigInt(0)),(-128,-128,BigInt(0)),
          (-128,127,BigInt(0)),(127,127,BigInt(0)),(0,-128,mask32),
          (1,1,BigInt("7fffffff",16)),(-1,1,BigInt("80000000",16)),
          (-128,-128,mask32),(-128,127,BigInt("80000000",16)))
          .map { case(a,b,c) => (repeated(a),repeated(b),c) }
        val inputs = directed ++ Seq.tabulate(1000) { i =>
          (BigInt(128,rng),BigInt(128,rng),if(i%2==0) BigInt(0) else BigInt(32,rng))
        }
        var pending: Option[BigInt] = None
        var expected: Option[BigInt] = None
        var checks = 0
        def tick(a: BigInt,b: BigInt,c: BigInt,e1: Boolean,e2: Boolean): Unit = {
          dut.io.vs1.poke(a.U);dut.io.vs2.poke(b.U);dut.io.acc.poke(c.U)
          dut.io.enable1.poke(e1.B);dut.io.enable2.poke(e2.B)
          if(e2) expected=pending
          if(e1) pending=Some(oracle(a,b,c))
          dut.clock.step()
          expected.foreach { x => dut.io.result.expect(x.U);checks+=1 }
        }
        for((a,b,c) <- inputs) tick(a,b,c,true,true)
        tick(0,0,0,false,true)
        for((a,b,c) <- inputs) tick(a,b,c,rng.nextInt(4)!=0,rng.nextInt(4)!=0)
        tick(0,0,0,false,true)
        println(s"VDOT_ACC_CHISEL_PASS csa=$carrySave prefix=$prefix retime=$retime inputs=${inputs.size} checked=$checks")
      }
    }
  }
}
