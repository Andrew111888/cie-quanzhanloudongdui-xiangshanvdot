# 报告、视频、绑定与提交包生成

这些入口整理真实验收证据，不代替处理器构建和测试。执行顺序如下；实际目录参数以本轮报告为准，不能把占位路径当作已有结果。

```bash
# 完整干净验收生成acceptance.json后，整理最终文档与原始CSV。
python3 scripts/summarize_acceptance.py /absolute/path/to/completed-acceptance

# 三个录屏入口必须使用已完成的干净验收。
export VDOT_REPRO_ROOT=/absolute/path/to/independent-checkout
export VDOT_ACCEPTANCE_DIR=/absolute/path/to/completed-acceptance
python3 scripts/record_terminal.py scripts/demo_stage1.sh --output output/video-stage1
python3 scripts/record_terminal.py scripts/demo_stage2.sh --output output/video-stage2
python3 scripts/record_terminal.py scripts/demo_stage3.sh --output output/video-stage3
```

先审阅所有文档、原始数据及录屏，再提交最终源码，保持Git工作区干净。绑定器比较处理器、NEMU、资源、工作负载、配置和关键构建/分析入口的字节；允许并记录后续报告/演示工具增加。子模块比较路径、SHA和初始化状态，不把不同克隆中的git-describe标签当作代码差异。rtl/中的两份生成模块另与本次完整构建的实际文件、FIR及补丁摘要比较，不把来源未明的生成文件混入交付。

```bash
python3 scripts/bind_evidence.py /absolute/path/to/completed-acceptance \
  --output reports/final-source-binding.json
bash scripts/render_reports.sh --binding reports/final-source-binding.json
```

PDF入口需要ReportLab，本机已验证4.4.9；版面复核使用Poppler和pypdf 6.10.0。启动脚本依次使用VDOT_PDF_PYTHON、已有系统Python或已安装的Codex依赖环境，不修改系统Python。其他机器可在独立Python虚拟环境安装ReportLab并设置VDOT_PDF_PYTHON。还需要DejaVu和Droid Sans Fallback字体、ImageMagick的SVG渲染。没有binding参数时仅生成标注待完成项的开发审阅稿；正式版写入output/pdf-release，须重新渲染并目视检查所有页。

录屏依赖和隔离显示方式见VIDEO_PLAN.md。视频、脚本、终端日志、实际退出码、源码前后清单与MP4参数一起保存；必须检查完整播放/抽帧、可读性和源摘要。工具预检短片不作为赛题视频。

```bash
python3 scripts/package_submission.py --binding reports/final-source-binding.json \
  --stage1-video output/video-stage1 --stage2-video output/video-stage2 \
  --stage3-video output/video-stage3 --output output/submission-package
```

该入口生成四类ZIP和SHA256SUMS，核对报告、视频及验收身份，检查ZIP完整性和450MB内部上限。证明材料包含原始环境输出，仅用于官网评审上传；公有源码包只使用Git跟踪文件，不包含private/、原始运行日志或报名个人资料。

只有包完整并绑定当前源码，才执行本地加密准备。该入口采用已与官方仓库比对的公钥和指纹，读取private/下用户确认的联系信息，明文保持0600，只打印输出目录；不执行推送、PR或官网提交。

```bash
python3 scripts/prepare_encrypted_submission.py --packages output/submission-package \
  --official-key reports/official-public-key-20261105.asc
```

只将生成的submission.asc放入官方脚本指定的赛题/队伍目录。提交前再次核对所有材料、仓库提交与阶段完成情况；上传与加密准备是不同步骤，不能以ZIP或密文存在推定官网已接收。
