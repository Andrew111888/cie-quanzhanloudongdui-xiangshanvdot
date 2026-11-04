# 香山昆明湖 V2 vdot 指令项目

2026 CIE 赛题独立工程，队伍：全栈漏洞队。当前为开发中状态，尚未满足完整提交条件。

赛题：[官方说明](https://rv.cie.org.cn/direction?id=8)。指令结果位宽等赛题未明确事项采用的暂定解释见 [contract.json](contract.json) 和 [待确认问题](docs/QUESTIONS.md)，尚未获得赛题方确认。

当前已完成数据通路级 Verilator 测试和 NEMU 独立运行测试；还没有成功生成全核仿真器，阶段一波形、整核 vdot、RTL/NEMU 协同仿真和 RTL 性能对比均未完成。不得将这些工作标记为通过。

`vdot_vstart_probe` 是独立探测程序：它尝试在非零 `vstart` 下执行普通 `vmul`。固定版本的 NEMU 原有实现对此报非法指令，因此该探测在 NEMU 中停止；这不是 vdot 主回归的通过项，也不单独证明 NEMU 违反规范。香山整核尚未构建，不能据此判断两者行为是否一致，待可运行原版整核后再比较。

全核构建继续采用官方 `MinimalConfig`，通过 `DISABLE_PERF=1 DISABLE_ALWAYSDB=1` 减少仿真统计与数据库逻辑。此前的 `VdotSimConfig` 精简实验还遇到软 PTW 和缓存索引问题，不作为可用配置。

实现说明见 [设计文档](docs/DESIGN.md)，当前工具、构建命令和限制见 [构建与运行记录](docs/BUILDING.md)。

`patches/` 保存相对固定上游版本的源代码改动，`workloads/` 是裸机测试与基准程序，`tests/` 是独立语义参考模型。编译工具和上游仓库保存在本地 `tools/` 与 `third_party/`，默认不上传。

提交准备：作品仓库已创建，代码在三个阶段验收通过后发布；提交信息模板见 [submission-info.template.txt](docs/submission-info.template.txt)。真实联系邮箱只填写在本地专用文件中，通过官方公钥加密后按指南提交，明文不要放入公开仓库。
