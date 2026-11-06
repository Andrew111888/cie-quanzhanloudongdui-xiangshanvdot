# 报告与数据整理

报告正文位于docs/submission/和[完整实验报告](累加融合实验结果.md)，原始结果位于docs/data/。运行日志保留输入、命令、退出码和源码摘要。

## 生成模块

```sh
python3 scripts/export_generated_rtl.py /absolute/path/to/completed-build-report
python3 scripts/check_repository.py --replay-patches
```

导出器核对完成的构建、FIR、补丁和模块摘要。当前共享路径写入rtl/，原平衡树构建写入rtl/baseline/。

## PDF

依赖版本见[报告依赖](累加报告依赖.txt)。`scripts/render_acc_report.py`从实验正文和完整验收回执生成PDF；输出后用Poppler逐页渲染检查。作者为全栈漏洞队，页脚为居中页码。

原三阶段PDF工具为`scripts/render_requirement_reports.py`，输入绑定、基础测试及证据目录通过其`--help`查看。报告生成和代码构建分别执行。

## 打包

`scripts/package_acc_experiment.py`整理源码、PDF、原始数据和SHA256清单，并检查ZIP完整性。打包使用已完成且摘要一致的实验回执。

录屏命令和讲解顺序见[录屏指南](RECORDING_GUIDE.md)。官网材料分类见[上传安排](UPLOAD_MANIFEST.md)。
