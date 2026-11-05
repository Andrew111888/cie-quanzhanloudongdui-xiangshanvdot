# 香山昆明湖 V2 vdot 指令项目

2026 CIE 赛题独立工程，队伍：全栈漏洞队。当前为开发中状态，尚未满足完整提交条件。

赛题：[官方说明](https://rv.cie.org.cn/direction?id=8)。指令结果位宽等赛题未明确事项采用的暂定解释见 [contract.json](contract.json) 和 [待确认问题](docs/QUESTIONS.md)，尚未获得赛题方确认。

全核仿真器现已成功构建。标准vadd、vdot定向整核、真实RTL/NEMU差分、向量状态单比特故障注入及恢复、1664条流水线压力测试均已取得实际通过证据。波形确认vdot功能单元输入至结果为2周期；60条RTL性能样本中，等价程序片段的中位数加速比为2.607–4.634。边界与原始证据见[阶段一波形](docs/STAGE1_WAVEFORM.md)、[差分验证](docs/DIFFTEST_CHECKS.md)、[性能报告](docs/PERFORMANCE.md)。

完整1000组随机输入已在修复驱动后通过整核差分，包括4000次合法随机vdot和1000次等价基线；退出码与4项输入校验均正确。另有波形证明3条已写回的错路vdot被分支冲刷且未提交。独立干净检出的全流程复现、三阶段录屏和最终打包仍在推进，尚未满足完整提交条件。当前服务及证据入口见[开发进度](docs/PROGRESS.md)。

`vdot_vstart_probe` 是独立探测程序：它尝试在非零 `vstart` 下执行普通 `vmul`。固定版本NEMU原有实现对此报非法指令；该探测不属于vdot主回归的通过项，也不单独证明规范问题。vdot自身的非零vstart非法行为已由整核差分检查。

全核构建继续采用官方 `MinimalConfig`，通过 `DISABLE_PERF=1 DISABLE_ALWAYSDB=1` 减少仿真统计与数据库逻辑。此前的 `VdotSimConfig` 精简实验还遇到软 PTW 和缓存索引问题，不作为可用配置。

实现说明见 [设计文档](docs/DESIGN.md)，当前工具、构建命令和限制见 [构建与运行记录](docs/BUILDING.md)。

独立检出已完成未修改原核的构建与vadd验证；vdot扩展核正在从空的硬件生成目录重建，详见 [干净复现记录](docs/CLEAN_REPRODUCTION.md)。代码与依赖来源见 [NOTICE](NOTICE.md)。

官网四个栏目的逐项来源核对见 [要求核对记录](docs/REQUIREMENTS_AUDIT.md)，三组文档、三段录屏和代码提交的当前缺口见 [交付清单](docs/DELIVERY_CHECKLIST.md)。

`patches/` 保存相对固定上游版本的源代码改动，`workloads/` 是裸机测试与基准程序，`tests/` 是独立语义参考模型。编译工具和上游仓库保存在本地 `tools/` 与 `third_party/`，默认不上传。

提交准备：作品仓库已创建，代码在三个阶段验收通过后发布；提交信息模板见 [submission-info.template.txt](docs/submission-info.template.txt)。真实联系邮箱只填写在本地专用文件中，通过官方公钥加密后按指南提交，明文不要放入公开仓库。
