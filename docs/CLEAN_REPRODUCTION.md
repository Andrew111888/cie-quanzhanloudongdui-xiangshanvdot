# 独立检出复现记录

## 2026-11-06：优化版的本轮重建

本轮完整功能、基础性能、波形及新增性能A/B复测全部通过。总回执reports/reproduction-recovery-swap-j4-20261106/status.json为passed、source_unchanged=true。保存的before共270条，本轮重新采集after共270条，合计540条；15份自动报告/数据从原始日志重算字节一致。

新的独立目录为/home/yh/cie/vdot-kmhv2-repro-20261106，固定作品提交4e5cfce9461e5870f266cff5b5347dd1265493c9。22个源码仓库按固定SHA从已缓存Git对象作独立克隆；复用已校验工具包、Conda环境和Maven下载缓存，禁用ccache。没有复制上一目录的RTL、C++、对象文件、NEMU二进制或模拟器，不声称全新操作系统或无下载缓存验证。准备清单在reports/preparation.json；目录时间戳使用UTC，报告日期使用北京时间。

从源码重新执行Python测试、Chisel数据通路测试、全部工作负载构建、NEMU独立程序及参考库构建，软件阶段均已通过。新构建的benchmark_rvv.bin、dot_memory.bin与flash.bin和此前对照输入逐字节一致，检查记录为reports/independent-reproduction-20261106/fresh-workload-hash-check.json。

| 阶段 | 实际结果与资源 | 原始证据 |
|---|---|---|
| Chisel/CHIRRTL | 退出0；10分43.10秒；最大RSS 4104264KiB | reports/vdot-build-20261105T163254Z-4164408/chisel-time.txt |
| firtool | 退出0；5分37.32秒；最大RSS 4438832KiB；独立16GiB文件映射池 | 同目录firtool-time.txt与命令 |
| 首次原生FST模型 | 6400MiB进程组上限处退出137，原失败状态保留 | 同目录compile-exit-status.txt |
| 文件堆模型尝试 | trace-depth=12及10两次因磁盘写回过慢被人工停止，均不计成功 | reports/model-resume-20261106T012148Z-181611与model-resume-20261106T013440Z-188153 |
| 原生模型恢复 | 启用临时系统交换空间；MemoryMax=8G、MemorySwapMax=2G；原生jemalloc、O1、inline-mult=1、FST层级10；生成后进入C++ | reports/model-native-swap-20261106T020712Z；并行度调整的人工停止另有deliberate-stop.json |
| C++续编译及链接 | 从2路改为4路；退出0；本段15分11.40秒，单子进程最大RSS 1225880KiB；复用本目录自己的已完成对象 | reports/model-native-swap-j4-20261106T021634Z |

15分11.40秒只计最后一段续编译，不能作为从零完整构建耗时。编译选项中仅生成DecodeUnit的宿主C++使用O0，其余快速对象使用O2。交换空间只用于宿主资源管理；状态查询因swapon不支持--json而失败后，改读内核/proc/swaps确认8GiB交换文件已启用，没有重复创建，也没有修改fstab。

reports/completed-build-20261106/composite-build.json逐项关联本轮成功的Chisel、firtool、原生生成与续编译，保留最初退出137和人工停止记录。源摘要、FIR摘要在恢复前后校验一致；没有伪造一次重新运行的Chisel或将失败日志改成通过。

本轮FIR SHA256为fa5e68cce015dc81e561d9f0bff3f0c565368c2e10a17df4a443c92fcea757ad；完成链接的emu SHA256为2f23052bb8407d837e1251faaed6e1890b765e3f33f682939a341eacaf87eb6d。独立生成的1868个SV模块与开发目录优化版比较，1867个一致，唯一差异是诊断打印LogPerfEndpoint；DecodeUnit、VIMacU与VdotDatapath字节一致。

本轮原始运行和验收状态保存在reports/reproduction-recovery-swap-j4-20261106/。正常功能验收使用本轮重新构建的NEMU参考库；性能A/B为了严格固定参考库，使用此前保存且校验过的同一reference.so。两类证据分别标记，不将A/B复用的旧库冒充本轮新构建库。

完整验收回执为reports/acceptance-20261106T023150Z-228441/acceptance.json，status=passed、source_unchanged=true。本轮新正常参考库SHA256为95faff9c9a0182e21d4820f405eade091ea7c3ec531382899e3ec1adf634b4d7；A/B固定参考库为baa2f11e3190d4dd3e7d6107c46ca6795c9b574978a070fdd7bdfafaf8372225。

| 本轮完整验收项 | 实际完成内容 |
|---|---|
| 标准向量与基础输入 | vadd、6组正负/边界输入、5种模式、7种非法形式及寄存器边界通过 |
| 完整随机 | 1000组×5模式，4000次合法vdot与1000次等价基线；786591条指令/593917周期 |
| 完整流水压力 | 64组、1664条vdot；28次taken、36次not-taken；290027条指令/181649周期 |
| 真实比较器反例 | 正常→错误→恢复；v12_low的REF9/DUT8、ABORT及退出1均被核实 |
| 基础性能 | 全部60条RTL样本通过；完整片段中位数加速比2.607至4.634 |
| 本轮真实FST | vdot输入至结果2周期；3条已写回错路指令被冲刷且未提交；5组×8条独立突发间隔1周期 |
| 波形接口与来源 | 3份FST各保留825个所需信号；关键输入摘要、PC/ROB动态区间和物理目的均核对 |

诊断窗口按28000周期预算停止，功能验收器实际拒绝其作为功能PASS；该窗口仅用于波形分析。完整压力程序另有GOOD TRAP和退出0。最终生成的CSV、时序图与来源索引见FINAL_RESULTS.md和data/clean/provenance.json。

## 2026-11-05：历史原核与首次扩展核复现

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

## vdot扩展核：完整构建与验收均已通过

在源提交3424efe下应用两个固定补丁，重放后4个香山文件和5个NEMU文件与补丁一致。Python4项、独立Chisel/Verilator数据通路、全部裸机工作负载构建及NEMU的vadd、vdot smoke/完整随机、latency、pipeline、register、benchmark功能均已通过，证据在独立目录reports/extension-preparation/。

重新构建的扩展NEMU参考库SHA256为baa2f11e3190d4dd3e7d6107c46ca6795c9b574978a070fdd7bdfafaf8372225；不能将开发目录83fd…的库摘要套用到新二进制。

原核生成目录已移动到build/pristine-generated，扩展核从空的XiangShan/build目录生成。构建报告为reports/vdot-build-20261105T050232Z-3720179/，命令显式VDOT_COMPILE_MEMORY_MAX=7G，其余配置为BUILDING.md的单核MinimalConfig和FST。该构建已正常完成，BUILD_COMPLETE、compile退出0及模拟器摘要重验均通过；新emu SHA256为dd1f0323f96d567e26e9ba25336db5f9cbcc3a9ebb55821665110fc993e30e31。

| 宿主构建阶段 | 实际墙钟耗时 | 最大RSS（KiB） | 退出码 |
|---|---:|---:|---:|
| Chisel/CHIRRTL | 5分38.35秒 | 4535272 | 0 |
| firtool | 6分02.43秒 | 6093400 | 0 |
| Verilator模型生成及C++编译/链接 | 1小时19分36秒 | 6003044 | 0 |

上述为各阶段/usr/bin/time原始计量，包含宿主I/O等开销，不是处理器指令延迟。扩展核FIR SHA256为9aca2ac7704e2e6a28dbd62cfdb81e6575686f45d16ebaa69ebf9bf94dc8d77e。rtl/中的生成模块与该构建逐字节对应，完整平台RTL仍由脚本从固定源码重新生成。

完整验证目录为reports/acceptance-20261105T063406Z-3723760/。verify_reproduction.sh已正常完成，acceptance.json记录status=passed、source_unchanged=true，后台服务退出0。7项整核运行均有完成标记、Difftest、GOOD TRAP、原始退出0和输入摘要复核；故障参考库反例与恢复另行验证。

| 完整验收项 | 实际结果 |
|---|---|
| 标准vadd、vdot smoke与寄存器边界 | 均通过，包含v0/v31、正负数、边界值和7种非法形式 |
| 固定随机 | 1000组×5模式，4000次合法随机vdot及1000次基线；786591指令/593917周期 |
| 流水压力 | 64组、1664条vdot，28次taken/36次not-taken；290027指令/181649周期 |
| 真实比较器反例 | REF9/DUT8的v12_low差异、ABORT、退出1；正确/错误/恢复三次输入摘要受控 |
| 性能 | 60条RTL样本完整通过，片段中位数加速比2.607–4.634 |
| 实际波形 | vdot输入至结果2周期；3条已写回错路指令未提交；5组×8条独立突发的握手间隔1周期 |
| 最终源码 | 构建与全部验收期间，平台、资源、项目关键输入的前后摘要一致 |

控制FST另用28000周期预算采集。该诊断按预算停止，未记作功能PASS；只有在与完整压力运行4项输入SHA相同时才用于分析。全部正式结果、CSV和FST来源摘要见FINAL_RESULTS.md及data/clean/provenance.json。三段真实录屏分别为62.7、101.7、122.7秒，命令退出0、源码前后摘要不变。

## 真实失败与修复

1. 新目录缺少out，直接调用MillMain时打开锁失败：启动器先创建目录；原失败命令复测通过。
2. 冷编译315个Rocket Chip源码时384MiB工具堆OOM：默认改为2GiB；同目标及主核源码全部通过。8GiB是硬件生成子进程堆，不代表Mill堆。
3. 原核文件映射模型生成受磁盘回写拖慢：进程组上限从5500MiB在线调至7GiB，记录memory-limit-adjustment.json。改用普通分配器的7GiB限时资源试验被进程组OOM终止，单独分类为失败探测；原模型暂停后恢复，最终正常完成。
4. CHIRRTL到firtool的第一次长运行被停止：恢复门禁核对源身份与FIR；故意提供错误FIR摘要时被拒绝，见主工程reports/resume-guard-negative.log。

以上资源实验只影响宿主构建方式，不改变RTL架构时序，也不用于计算处理器加速比。最终归档用source-binding.json关联上述实际构建提交与最终源码提交，核对处理器、参考模型、工作负载、配置、关键脚本及生成RTL，不改写早期运行的身份。
