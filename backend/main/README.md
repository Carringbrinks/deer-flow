# 专利导航报告 — 生成 & 转换

## 第一步：生成报告

激活环境，启动交互式脚本：

```bash
cd /data2/deer-flow/backend
source .venv/bin/activate
python main/generate_report.py
```

启动后终端显示如下界面，记下 `线程` ID（后续所有的输出产物都在这个路径下）：
例如：/data2/deer-flow/backend/main/.deer-flow/users/default/threads/59d76d096edc45569202109836ed3a17
```
==================================================
交互运行模式
模型: Qwen3.6-27B
线程: 59d76d096edc45569202109836ed3a17
思考模式: 开
计划模式: 开
子代理: 关
输入 'quit' 或 'exit' 停止
上传文件方式:
  upload /path/to/file1 /path/to/file2 -- 可选的提示消息
如果省略消息，将发送默认上传提示。
日志: run_agent.log (日志级别=INFO)
==================================================
```

在 `You:` 提示符后输入 `upload` 命令启动报告生成：

```
You: upload /data2/deer-flow/backend/main/example/patent-navigation-request-list-sample.md
```

程序将自动读取需求文档并开始逐章生成。生成过程中可能耗时较长（取决于报告复杂度），请耐心等待（2-4小时）。生成完毕后，终端会打印最终交付文件的虚拟路径与物理路径对应关系：

```
[新保存的文件]
  - /mnt/user-data/outputs/report.md
    → /data2/deer-flow/backend/main/.deer-flow/users/default/threads/59d76d096edc45569202109836ed3a17/user-data/outputs/report.md
  - /mnt/user-data/outputs/abstract.md
    → /data2/deer-flow/backend/main/.deer-flow/users/default/threads/59d76d096edc45569202109836ed3a17/user-data/outputs/abstract.md
  - /mnt/user-data/outputs/refs.md
    → /data2/deer-flow/backend/main/.deer-flow/users/default/threads/59d76d096edc45569202109836ed3a17/user-data/outputs/refs.md
```

> 技能采用“构建目录 + 交付目录”分离的布局：所有过程产物都写在 `workspace/patent_navigation/`，只有最终交付文件才复制到 `outputs/`。这是因为 `present_files` 只接受 `outputs/` 下的文件。

### 以下为宿主机上对应的实际目录结构

| 目录 | 说明 |
|------|------|
| `workspace/patent_navigation/parts/` | 逐章生成的中间产物，每章对应 3 个文件：正文 (`.md`)、参考文献 (`_refs.md`)、摘要 (`_abstract.md`) |
| `workspace/patent_navigation/assets/` | 图表及绘图原始数据，`charts/` 存放图片，`data/` 存放 CSV/JSON 数据 |
| `workspace/patent_navigation/scripts/` | 绘图与合并脚本 |
| `workspace/patent_navigation/merged/` | 程序自动合并后的中间结果，供后续步骤使用或人工检查 |
| `workspace/patent_navigation/final/` | **最终文件暂存区**，包含完整的 Markdown 报告、全文摘要和参考文献 |
| `outputs/` | **最终交付目录**，仅存放 `report.md`、`abstract.md`、`refs.md`（以及可选的 `report.docx`），供 `present_files` 呈现 |

```
.deer-flow/users/default/threads/{thread_id}/user-data/
│
├── workspace/                          ← 工作目录（所有过程文件）
│   └── patent_navigation/
│       ├── parts/                      ← 逐章生成产物
│       │   ├── part_01_chapter01.md
│       │   ├── part_01_chapter01_refs.md
│       │   ├── part_01_chapter01_abstract.md
│       │   ├── part_02_chapter02.md
│       │   ├── part_02_chapter02_refs.md
│       │   ├── part_02_chapter02_abstract.md
│       │   ├── ...
│       │   └── part_NN_chapterNN_abstract.md
│       │
│       ├── assets/                     ← 图表与数据资源
│       │   ├── charts/                 ← 图表图片文件（PNG / SVG）
│       │   │   ├── fig_1_1_xxx.png
│       │   │   ├── fig_1_2_xxx.png
│       │   │   ├── fig_2_1_xxx.png
│       │   │   └── ...
│       │   │
│       │   └── data/                   ← 绘图原始数据（CSV / JSON）
│       │       ├── data_1_1_xxx.csv
│       │       ├── data_1_2_xxx.csv
│       │       ├── data_2_1_xxx.csv
│       │       └── ...
│       │
│       ├── scripts/                    ← 绘图与合并脚本
│       │
│       ├── merged/                     ← 中间合并结果（强制生成）
│       │   ├── abstracts.md            ← 各章摘要整合后的全文摘要（初版）
│       │   ├── body.md                 ← 所有章节正文合并结果
│       │   └── references.md           ← 去重+重编号后的参考文献全集
│       │
│       └── final/                      ← 最终文件暂存区
│           ├── report.md               ← 最终整合报告（摘要 + 正文 + 参考文献）
│           ├── abstract.md             ← 最终润色后的全文摘要
│           ├── refs.md                 ← 最终参考文献
│           └── report.docx             ← 可选（pandoc 可用时生成）
│
└── outputs/                            ← 交付目录（仅最终文件）
    ├── report.md
    ├── abstract.md
    ├── refs.md
    └── report.docx                     ← 可选
```


---

## 第二步：转换 docx（修复图片路径）

`report.md` 中的图片路径是 sandbox 虚拟路径 `/mnt/user-data/workspace/patent_navigation/assets/charts/...`，需要替换为宿主机物理路径后再用 Pandoc 生成 docx。

**建议直接对构建目录中的 `final/report.md` 运行转换**：这样中间文件 `report_local.md` 会留在构建目录，不会污染 `outputs/`；docx 通过 `-o` 指定到交付目录。

```bash
python main/convert_to_docx.py \
  .deer-flow/users/default/threads/<线程ID>/user-data/workspace/patent_navigation/final/report.md \
  -o .deer-flow/users/default/threads/<线程ID>/user-data/outputs/report.docx
```

脚本会自动：
1. 将 md 中的 `/mnt/user-data` 替换为宿主机物理路径，在同目录保存为 `report_local.md`
2. 调用 Pandoc 生成带目录、章节编号的 `report.docx`（输出到 `-o` 指定路径）

运行示例：

```
============================================
  Patent Navigation Report → DOCX
============================================
  输入文件:       .../user-data/workspace/patent_navigation/final/report.md
  替换后 md:      .../user-data/workspace/patent_navigation/final/report_local.md
  输出 docx:      .../user-data/outputs/report.docx
  目标基础路径:   .../user-data
  虚拟路径前缀:   /mnt/user-data
============================================

>>> 步骤 1/2: 替换图片路径并保存新 md
    /mnt/user-data → .../user-data
    共替换 63 处路径 → .../user-data/workspace/patent_navigation/final/report_local.md

>>> 步骤 2/2: Pandoc 生成 DOCX

============================================
  ✓ 转换成功!
  .../user-data/outputs/report.docx
  文件大小: 7.16 MB
============================================
```

> **提示**：如果generate_report.py代码运行终端，不需要退出终端交互，直接输入“继续生成即可”。
