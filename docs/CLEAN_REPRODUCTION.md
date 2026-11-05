# 独立检出复现记录

核对日期：2026-11-05。根目录为/home/yh/cie/vdot-kmhv2-repro-20261105。该目录从本机作品Git创建独立检出，再从官方仓库按SHA获取上游及资源；没有复制开发目录的生成RTL、C++、目标文件或模拟器。

同机复用已校验的Mill工件、开发依赖包、固定Conda工具环境、firtool及Maven下载缓存。原核Scala依赖在新目录冷编译；随后应用vdot补丁时复用该独立目录自己的Scala依赖缓存，但移动整个原核build目录，扩展核重新生成RTL和C++。这不是全新操作系统或无下载缓存的验证。

## 未加vdot的原核：已通过

| 项目 | 结果与证据 |
|---|---|
| 固定源码 | XiangShan 7b16188f7f18a97be69c9b1a2dae8a446eec3b47；NEMU d772a9d9e06f663d529bd1c6518480c1ee59ded2；两仓库受版本控制文件无改动 |
| 新目录准备 | 主工程reports/clean-prepare-driver.log；固定资源、工具包SHA校验及原版NEMU参考库通过 |
| Scala/CHIRRTL | 独立目录reports/vdot-build-20261105T023049Z-3607811/，Chisel退出0；FIR摘要6d97444c3d34e49ba30f8b6d72e0c5a6704ff27d1c5000e77ff0a4adbd688189 |
| 中断恢复 | firtool阶段10:50被停止，保留未完成记录；随后91245d7入口校验相同源码、配置及FIR后恢复；未伪造新的Chisel运行 |
| firtool、Verilator、C++ | reports/vdot-build-20261105T032838Z-3639339/，firtool与compile退出0、完整BUILD_COMPLETE、源摘要前后一致 |
| 原核vadd | reports/rtl-vadd_test-20261105T045747Z-3710923/，VADD_PASS、真实Difftest、GOOD TRAP、退出0 |
| 原核FST | SHA256 08ff4d757cc0445bd579a708515574c48a47bb298969bbddcc4988865908b503；提取后端接口成功 |
| 保存产物 | build/pristine/emu、reference.so、vadd_test.bin、flash.bin；reports/pristine-preserved.sha256核对全部正确 |

原核emu SHA256为b887f745a2c04b9bc2db4e9b8d0d47125068dcf69772a403b5e9677a01b1a878，原版NEMU参考库为88c6eb01871691981e2e5e095e337239acad63d006489ace4248fd61abb513de。该二者仅证明标准向量原核环境，不具有vdot实现。

## vdot扩展核：当前在构建

在源提交3424efe下应用两个固定补丁，重放后4个香山文件和5个NEMU文件与补丁一致。Python4项、独立Chisel/Verilator数据通路、全部裸机工作负载构建及NEMU的vadd、vdot smoke/完整随机、latency、pipeline、register、benchmark功能均已通过，证据在独立目录reports/extension-preparation/。

重新构建的扩展NEMU参考库SHA256为baa2f11e3190d4dd3e7d6107c46ca6795c9b574978a070fdd7bdfafaf8372225；不能将开发目录83fd…的库摘要套用到新二进制。

原核生成目录已移动到build/pristine-generated，扩展核从空的XiangShan/build目录生成。当前构建报告为reports/vdot-build-20261105T050232Z-3720179/，命令显式VDOT_COMPILE_MEMORY_MAX=7G，其余配置为BUILDING.md的单核MinimalConfig和FST。

主工程后台构建为vdot-extension-clean-20261105T0502.service，入口日志reports/extension-clean-driver.log；全量验证等待服务为vdot-extension-acceptance-20261105T0510.service。排队不表示通过。构建完成并通过输入摘要后，verify_reproduction.sh才执行真实差分、故障注入恢复、完整随机、压力、边界寄存器、性能与波形分析。

## 真实失败与修复

1. 新目录缺少out，直接调用MillMain时打开锁失败：启动器先创建目录；原失败命令复测通过。
2. 冷编译315个Rocket Chip源码时384MiB工具堆OOM：默认改为2GiB；同目标及主核源码全部通过。8GiB是硬件生成子进程堆，不代表Mill堆。
3. 原核文件映射模型生成受磁盘回写拖慢：进程组上限从5500MiB在线调至7GiB，记录memory-limit-adjustment.json。改用普通分配器的7GiB限时资源试验被进程组OOM终止，单独分类为失败探测；原模型暂停后恢复，最终正常完成。
4. CHIRRTL到firtool的第一次长运行被停止：恢复门禁核对源身份与FIR；故意提供错误FIR摘要时被拒绝，见主工程reports/resume-guard-negative.log。

以上资源实验只影响宿主构建方式，不改变RTL架构时序，也不用于计算处理器加速比。最终提交前仍须取得扩展核完整验收、录屏与报告的统一绑定。
