# Verilator 5.022 低内存构建路线核查

日期：2026-11-05。范围是本机 `Verilator 5.022 2024-02-24 rev conda-forge build 1` 和 Debian `libvmmalloc1 1.8-2`，只查本机帮助及官方对应版本源码。此研究没有启动或停止整核构建，也没有修改构建脚本或 RTL。下列建议不能当作整核构建成功证据。

## 首要发现：追加 -O1 没有撤销 -O3 的最大内联

当前低内存 wrapper 接收上游 `-O3`，再在尾部追加 `-O1`。在 **5.022** 中，两者会先后执行 `V3Options::optimize(3)` 和 `optimize(1)`；该函数只有 `level >= 3` 时才把 `m_inlineMult` 改成 `-1`，处理 `-O1` 时不恢复它。因此当前命令仍然保留最大内联，不能把它描述为已恢复默认内联门槛。[来源：v5.022 V3Options.cpp，第 1348–1351、2001–2031 行](https://github.com/verilator/verilator/blob/v5.022/src/V3Options.cpp#L2001)

该版本默认门槛是 **2000**。官方说明正数代表允许内联增加的操作数门槛，小于 1 则尽量全部内联；`-O3` 的慢优化目前正是将其设为 `-1`。[来源：v5.022 V3Options.h](https://github.com/verilator/verilator/blob/v5.022/src/V3Options.h#L305)、[v5.022 选项文档](https://github.com/verilator/verilator/blob/v5.022/docs/guide/exe_verilator.rst#L712)

优先候选是保留其余配置，只在所有 `-O` 参数之后显式设置 `--inline-mult 2000`。应先用小层级 RTL 对照验证参数残留，再进行唯一一次整核模型生成，比较峰值内存、耗时和模型可用性。**源码确认了参数残留；尚未证明显式恢复门槛就能使本机整核构建完成。** 更小的正数或 `-fno-inline` 可作为后续单变量实验；`0` 不能用来表示禁用内联。

## libvmmalloc 1.8：可用的旧版配置及其边界

官方 vmem 1.8 的分配器基于经过文件映射修改的 **jemalloc 3.6.0**，不能套用现代 jemalloc 的 decay 参数。[来源：README.libvmem](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/README.libvmem#L5)

该库构建时使用 `je_vmem_` 前缀，配置读取器使用前缀大写加 `MALLOC_CONF`。所以本机实际识别的环境变量是 **`JE_VMEM_MALLOC_CONF`**；`strings` 对本机库的检查也命中了该名字。普通 `MALLOC_CONF` 不能据此视为已配置了这个分配器。[来源：jemalloc.cfg](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/jemalloc.cfg#L2)、[配置读取代码](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/jemalloc.c#L603)

| 选项 | 1.8 源码确认的行为 | 对当前问题的判断 |
|---|---|---|
| `lg_dirty_mult:-1` | 配置解析接受 `-1`；`arena_maybe_purge` 在值为负数时直接返回；默认值为 3 | 禁止基于 dirty/active 比例触发的自动 arena purge，但不会禁止所有 chunk 回收路径的 purge |
| `narenas:1` | 配置解析接受大于等于 1 的值；pool 用该值确定自动 arena 数量 | 可以单独测试；不是已经证实的本机收益，不宜与其他参数同时改变 |
| `junk:false`、`zero:false` | 非 debug 默认 `junk=false`，`zero` 默认 false；相关选项还受编译期 fill 支持控制 | 已经关闭的填充不能再次消除；不能用它们取消 `calloc` 所要求的清零 |
| `dirty_decay_ms`、`muzzy_decay_ms`、`background_thread` | 不是这份旧版配置解析器提供的参数 | 不将现代 jemalloc 参数加入当前 `JE_VMEM_MALLOC_CONF` |

来源：[解析器及默认值](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/jemalloc.c#L747)、[自动 purge 的退出条件](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/arena.c#L869)、[默认 dirty 比例](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/include/jemalloc/internal/arena.h#L44)、[pool arena 初始化](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/pool.c#L92)。

`pages_purge` 在 Linux 对应路径调用 `madvise`，并针对文件映射标记内容为未清零；此函数本身没有用 `memset` 清零文件页。arena 的 purge 会调用它，chunk 回收也会独立调用它。[来源：chunk_mmap.c](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/chunk_mmap.c#L117)、[arena.c](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/arena.c#L997)、[chunk.c](https://github.com/pmem/vmem/blob/1.8/src/jemalloc/src/chunk.c#L273)

因此，**不能把当前大量文件写入直接归因为 purge 中的显式清零**。Linux 的 `MADV_DONTNEED` 对共享文件映射允许后续访问重新取回文件的最新内容，内核可延迟真正释放共享页。受限物理内存、反复访问文件页和页缓存回写的组合仍可能导致大量 I/O，但本轮没有用系统调用或页回写采样证明具体比例。[来源：Linux man-pages 的 madvise(2) 说明](https://github.com/mkerrisk/man-pages/blob/master/man2/madvise.2#L122)

主代理已做小型分配器探测：64MiB 活跃集、32 轮、192MiB 内存上限，默认配置约 0.44 秒/68MB 写入，`lg_dirty_mult:-1` 约 1.05 秒/177MB 写入，校验值一致。该探测**没有显示收益**，也不能替代整核负载测量；当前不据此切换真实构建的分配器配置。环境变量在初始化阶段读取，修改外部 shell 不会重新配置正在运行的进程。

`VMMALLOC_POOL_SIZE` 只是固定文件池容量，不能降低活跃工作集；该库原本针对 DAX 持久内存更有用，普通文件系统通过页缓存访问，其行为与增加真实 RAM 不同。[来源：libvmmalloc 1.8 手册](https://github.com/pmem/vmem/blob/1.8/doc/libvmmalloc/libvmmalloc.7.md)

## --hierarchical 需要选块，并且牺牲块内波形

固定 **v5.022** 的真实用法是：先在 HDL 标记 `/*verilator hier_block*/`，或在独立 Verilator 配置文件使用 `hier_block -module "模块名"`，再传 `--hierarchical`。仅加该命令行开关不会自动选择切分位置；源码发现没有任何标记块时直接返回。[来源：v5.022 分层用法](https://github.com/verilator/verilator/blob/v5.022/docs/guide/verilating.rst#L89)、[V3HierBlock.cpp](https://github.com/verilator/verilator/blob/v5.022/src/V3HierBlock.cpp#L348)

分层模型通过 `--lib-create` 为每个选定块生成库和包装层。一次初始规划加上每块及顶层的独立生成，可减少单次处理的模型规模；需要串行化这些子任务，避免同时占用内存。[来源：分层流程与并行规则](https://github.com/verilator/verilator/blob/v5.022/docs/guide/verilating.rst#L137)

该版本明确列出的限制包括：

- 块内信号不能追踪波形，且上层或其他块不能跨边界用点引用其内部。
- 分层边界不支持 modport；块内不允许延迟。
- 跨块传递生成时钟可能不正确；主机仿真速度可能低于全局调度的普通模型。

来源：[v5.022 分层限制](https://github.com/verilator/verilator/blob/v5.022/docs/guide/verilating.rst#L108)。

官方没有在此列出“任何 DPI 均不支持”的总禁令，库包装本身也使用 DPI。不过这不能证明香山当前 Difftest 导入、作用域及链接自动兼容；必须对拟选块逐一检查并实际完成整核差分。切出整个 core/backend 会失去本赛题所需的内部执行波形，因此分层构建不能直接替代阶段一的波形验收。[来源：--lib-create 的 DPI 库说明](https://github.com/verilator/verilator/blob/v5.022/docs/guide/exe_verilator.rst#L769)

当前建议将它保留为需要专门集成的后备路线，先验证显式内联门槛；本轮不改 HDL 或生成分层配置。

## 无波形及其他选项的真实作用

| 路线或选项 | 5.022 的真实作用 | 当前使用边界 |
|---|---|---|
| 不传 `--trace`/`--trace-fst` | 不创建 trace 声明/采样点及后续追踪模型；源码中的相应 pass 受 `opt.trace()` 条件控制 | 可能降低生成负担，具体峰值下降仍待测；无波形模型可先做功能/差分和性能，但不能产出阶段一波形 |
| `--trace-depth N` | 限制可追踪的层级深度 | 当前已使用 12；不能假定更浅仍包含译码至提交链路 |
| `--trace-max-array N`、`--trace-max-width N` | 限制数组深度及信号位宽，默认分别为 32 和 256 | 只减少追踪对象；若位宽压到 128 以下，会漏掉 128 位向量结果 |
| `--no-trace-params` | 禁止参数追踪 | 可以测试，不能保证显著降低整核峰值 |
| 配置文件 `tracing_on/off -scope ...` | 对指定作用域及深度启闭追踪；也支持按文件/行范围控制 | 可保留必要向量链路并排除其他波形；作用域和规则顺序需先小例验证，不能只凭猜测做全局白名单 |
| `--verilate-jobs 1` | 限制内部生成步骤并行度 | 与 C++ `make -j1` 是不同层面；需核对实际命令，不能因 make 串行就推断所有内部任务已串行 |
| `--output-split`、`--output-split-cfuncs`、`--output-split-ctrace` | 拆分生成的 C++ 文件、函数及追踪函数 | 主要帮助后续 C++ 编译，不是将整个输入 AST 拆成独立模型；不能保证消除当前尚未输出 C++ 时的峰值 |
| `-O0` 或 `-fno-inline` | 禁用全部模型优化，或仅禁用内联；相应开关应放在会重置优化布尔量的 `-O` 之后 | 作为后续单变量候选；关闭优化可能留下更大的未简化模型，不保证内存更低 |

来源：[trace 生成的条件分支](https://github.com/verilator/verilator/blob/v5.022/src/Verilator.cpp#L387)、[trace 选项](https://github.com/verilator/verilator/blob/v5.022/docs/guide/exe_verilator.rst#L1425)、[作用域控制](https://github.com/verilator/verilator/blob/v5.022/docs/guide/exe_verilator.rst#L2066)、[内部并行度](https://github.com/verilator/verilator/blob/v5.022/docs/guide/exe_verilator.rst#L1540)、[C++ 拆分选项](https://github.com/verilator/verilator/blob/v5.022/docs/guide/exe_verilator.rst#L922)。本机 `--help` 对 `trace-max-array` 和 `trace-max-width` 的一句描述存在互换，本文采用固定版本长文档及 `V3Options.h` 的值定义。

实施优先级为：先验证并显式恢复内联门槛；如仍失败，再单独评估无波形模型或缩小追踪范围；分配器配置与分层编译均保留为需证据支持的后备路线。每次只运行一个整核构建，保留退出状态、峰值内存、耗时、读写量和产物校验值，不把“未 OOM”当作构建完成。
