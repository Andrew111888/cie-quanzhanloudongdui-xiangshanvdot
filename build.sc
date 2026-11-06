import mill._
import mill.scalalib._

object datapath extends ScalaModule {
  def scalaVersion = "2.13.15"
  def ivyDeps = Agg(ivy"org.chipsalliance::chisel:6.7.0")
  def scalacPluginIvyDeps = Agg(ivy"org.chipsalliance:::chisel-plugin:6.7.0")
  def sources = T.sources {
    Seq(PathRef(millSourcePath / ".." / "src" / "Vdot.scala"))
  }
  object test extends ScalaTests with TestModule.ScalaTest {
    override def sources = T.sources {
      Seq(PathRef(os.Path(sys.env("MILL_WORKSPACE_ROOT")) / "datapath" / "test" / "src"))
    }
    def ivyDeps = super.ivyDeps() ++ Agg(ivy"edu.berkeley.cs::chiseltest:6.0.0")
    def forkArgs = Seq("-Xmx2g", "-XX:ActiveProcessorCount=2")
  }
}
