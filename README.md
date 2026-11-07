# 香山昆明湖 V2 向量点积指令设计

全栈漏洞队 · 西安电子科技大学

项目在昆明湖V2的128位向量通路中实现vdot.vv及独立编码的vdot.acc，复用现有译码、调度、读源、VIMacU、写回和提交通路。

- vdot.vv：低8对有符号int8点积，结果写低32位，高96位清零。
- vdot.acc：点积与旧目标低32位融合累加，按模2^32回绕，高96位清零。

两条指令共用8路乘法、压缩树和前缀加法器，采用两级流水。支持SEW=8、VLEN=128、LMUL=1、VL=8、vstart=0、无掩码。

## 文档

| 内容 | 入口 |
|---|---|
| 环境与构建 | [环境部署](docs/环境部署.md)、[复现说明](docs/复现说明.md) |
| 第一阶段 | [环境验证、日志及向量加法过程](docs/第一阶段文档.md) |
| 第二阶段 | [第二阶段文档](docs/第二阶段文档.md) |
| 第三阶段 | [第三阶段文档](docs/第三阶段文档.md) |
| 录屏 | [三阶段操作指南](docs/录屏指南.md) |

## 代码

| 目录 | 内容 |
|---|---|
| src/ | 点积与累加的Chisel数据通路 |
| patches/ | 相对固定上游的香山集成和NEMU完整改动 |
| rtl/ | 当前实际生成模块及资源对照所用原点积模块 |
| examples/、workloads/ | 基础、随机、流水、异常及性能程序 |
| datapath/、tests/、verification/ | Chisel、软件参考和独立算术验证 |
| scripts/、configs/ | 构建、运行和固定配置 |
| experiments/acc/ | 性能报告中使用的算术对照源码 |
| docs/data/ | 结果汇总和逐次周期CSV |

## 验证与结果

整核验证包含1000组唯一随机输入、22,318次合法点积执行、1664条累加流水、v0/v31及48例交叉异常。六项基础测试和错误参考检出、恢复均通过。

当前共享实现的vdot.vv与vdot.acc均已采集真实整核FST，输入到输出实测为2拍。协同仿真文档包含两种指令的输入、输出写回和提交截图，波形程序及分析入口见examples/vdot_wave.c和scripts/analyze_vdot_wave.py。

180条性能样本中，512轮下4/8条独立链的原路径/融合周期比为1.428/2.255，单链为0.862。含访存长点积K=32/128/512相对较快RVV的比例为1.124/0.983/0.892。适用条件见性能分析。

```sh
python3 scripts/check_repository.py
python3 -m unittest discover -s tests -v
```

完整日志、FST、ELF、反汇编及构建中间文件在本地留存。重新运行脚本产生的文件写入reports/和build/，不进入Git。源码和依赖许可见[NOTICE](NOTICE.md)及[LICENSE](LICENSE)。
