import chisel3._
import chiseltest._
import org.scalatest.flatspec.AnyFlatSpec
import xiangshan.backend.fu.vector.VdotDatapath

class VdotDatapathTest extends AnyFlatSpec with ChiselScalatestTester {
  behavior of "VdotDatapath"

  private def oracle(a: BigInt, b: BigInt): BigInt = {
    def byte(x: BigInt, i: Int): Int = {
      val v = ((x >> (i * 8)) & 255).toInt
      if (v < 128) v else v - 256
    }
    BigInt((0 until 8).map(i => byte(a, i) * byte(b, i)).sum) & BigInt("ffffffff", 16)
  }
  private def repeatByte(x: Int): BigInt = (0 until 16).map(i => BigInt(x & 255) << (i * 8)).sum

  it should "check every random input and preserve stage data under independent enables" in {
    test(new VdotDatapath).withAnnotations(Seq(VerilatorBackendAnnotation)) { dut =>
      val rng = new scala.util.Random(20261104L)
      var pending: Option[BigInt] = None
      var expected: Option[BigInt] = None
      dut.io.enable1.poke(false.B)
      dut.io.enable2.poke(false.B)
      dut.clock.step()
      val directed = Seq((1,1), (-1,1), (-128,-128), (-128,127), (127,127), (0,-128))
        .map { case (a,b) => (repeatByte(a), repeatByte(b)) }
      val inputs = directed ++ Seq.fill(1000)((BigInt(128, rng), BigInt(128, rng)))
      // Every arithmetic input must enter the pipeline and be checked. A random
      // enable-only loop can discard some inputs and does not prove this count.
      for ((a, b) <- inputs) {
        dut.io.vs1.poke(a.U)
        dut.io.vs2.poke(b.U)
        dut.io.enable1.poke(true.B)
        dut.io.enable2.poke(true.B)
        expected = pending
        pending = Some(oracle(a, b))
        dut.clock.step()
        expected.foreach(x => dut.io.result.expect(x.U))
      }
      dut.io.enable1.poke(false.B)
      dut.io.enable2.poke(true.B)
      dut.clock.step()
      dut.io.result.expect(pending.get.U)
      expected = pending
      for (((a, b), index) <- inputs.zipWithIndex) {
        // Independently stress the two physical stage enables.
        val enable1 = index < directed.size || rng.nextInt(4) != 0
        val enable2 = index < directed.size || rng.nextInt(4) != 0
        dut.io.vs1.poke(a.U)
        dut.io.vs2.poke(b.U)
        dut.io.enable1.poke(enable1.B)
        dut.io.enable2.poke(enable2.B)
        if (enable2) expected = pending
        if (enable1) pending = Some(oracle(a, b))
        dut.clock.step()
        expected.foreach(x => dut.io.result.expect(x.U))
      }
      dut.io.enable1.poke(false.B)
      dut.io.enable2.poke(true.B)
      dut.clock.step()
      dut.io.result.expect(pending.get.U)
      println(s"VDOT_DATAPATH_PASS arithmetic_cases=${inputs.size} enable_stress_cycles=${inputs.size}")
    }
  }
}
