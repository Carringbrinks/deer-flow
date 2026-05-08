
# 专利导航报告合并协议

本协议定义专利导航报告的强制合并流程。执行第3步“整合输出”时，必须先读取本文件，并按本文件完成所有中间产物与最终交付文件。

## 核心原则

先分类合并（摘要 / 正文 / 参考文献）→ 生成中间汇总文件 → 再统一合并为最终报告。严禁跨步、跳过 `outputs/merged/` 或直接拼接最终报告。

## 输入与输出结构

合并阶段必须使用以下输出范式：

```
outputs/
├── parts/                      ← 存放所有中间过程文件（逐章生成产物）
│   ├── part_01_chapter01.md
│   ├── part_01_chapter01_refs.md
│   ├── part_01_chapter01_abstract.md
│   ├── part_02_chapter02.md
│   ├── part_02_chapter02_refs.md
│   ├── part_02_chapter02_abstract.md
│   ├── ...
│   └── part_NN_chapterNN_abstract.md
│
├── assets/                     ← 图表与数据资源
│   ├── charts/                 ← 图表图片文件（PNG / SVG）
│   │   ├── fig_1_1_xxx.png
│   │   ├── fig_1_2_xxx.png
│   │   ├── fig_2_1_xxx.png
│   │   └── ...
│   │
│   └── data/                   ← 绘图原始数据（CSV / JSON）
│       ├── data_1_1_xxx.csv
│       ├── data_1_2_xxx.csv
│       ├── data_2_1_xxx.csv
│       └── ...
│
├── merged/                     ← 中间合并结果（强制生成）
│   ├── abstracts.md            ← 各章摘要整合后的全文摘要（初版）
│   ├── body.md                 ← 所有章节正文合并结果
│   └── references.md           ← 去重+重编号后的参考文献全集
│
└── final/                      ← 最终交付文件夹（仅存最终成果）
    ├── report.md               ← 最终整合报告（摘要 + 正文 + 参考文献）
    ├── report.docx             ← Word版本（由 report.md 转换）
    ├── abstract.md             ← 最终润色后的全文摘要（可基于 merged/abstracts.md 再优化）
    └── refs.md                 ← 最终参考文献（来自 merged/references.md）
```

## 标准化合并流程

### 步骤 A：合并章节摘要 → abstracts.md

输入来源：
- `outputs/parts/*_abstract.md`

处理规则：
1. 按章节编号顺序读取（chapter01 → chapterNN）。
2. 去除每章摘要中的标题，如 `### 本章摘要`。
3. 提取关键信息并压缩整合，禁止简单拼接。
4. 统一语言风格，形成连贯的全文摘要。
5. 合并后的摘要不得保留小标题或章节划分，必须是一个整体段落或几个连续段落，禁止分章展示。
6. 不得包含图片语法或 `[citation:...]` 标记。

输出格式：

```markdown
# 摘要

<整合后的全文摘要（3000-5000字）>
```

保存路径：
- `outputs/merged/abstracts.md`

### 步骤 B：合并所有章节正文 → body.md

输入来源：
- `outputs/parts/part_XX_chapterXX.md`

处理规则：
1. 按章节编号顺序读取。
2. 原样拼接正文内容。
3. 保留原始 Markdown 标题结构。
4. 不插入摘要或参考文献。
5. 保留正文中的图表 Markdown 语法和引用标记。

保存路径：
- `outputs/merged/body.md`

### 步骤 C：合并参考文献 → references.md

输入来源：
- `outputs/parts/*_refs.md`

处理规则：
1. 提取所有文献条目，标准格式为 `1. [名称](URL)`；无 URL 时可使用 `1. 文献名称`。
2. 执行去重：优先按 URL 去重；无 URL 时按名称去重。
3. 保留首次出现项。
4. 全局重新编号（1 → N）。
5. 不得保留各章原始编号或重复分组标题。

输出格式：

```markdown
# 参考文献

1. [文献A](URL)
2. [文献B](URL)
```

保存路径：
- `outputs/merged/references.md`

### 步骤 D：生成最终交付文件

必须按以下顺序生成最终交付文件：

1. 将 `outputs/merged/abstracts.md` 复制或同步为 `outputs/final/abstract.md`，可在不改变事实依据的前提下进行最终润色。
2. 将 `outputs/merged/references.md` 复制或同步为 `outputs/final/refs.md`。
3. 按以下顺序拼接生成 `outputs/final/report.md`：
   - `outputs/final/abstract.md`
   - `outputs/merged/body.md`
   - `outputs/final/refs.md`
4. 由 `outputs/final/report.md` 转换生成 `outputs/final/report.docx`。

`outputs/final/report.md` 必须仅由摘要、正文、参考文献三部分组成，不得混入章节草稿、临时说明、评估记录或其他过程性文本。

## Word 转换

### 转换命令

**重要前提**：`report.md` 中的图片路径均以 `outputs/assets/...` 开头，为确保 Pandoc 能正确解析图片路径，必须在 `outputs` 文件夹的**父目录**（项目根目录）执行转换命令。

```bash
# 进入 outputs 的父目录（项目根目录）
cd /path/to/your/project

# 执行转换
pandoc outputs/final/report.md \
  -o outputs/final/report.docx \
  --toc \
  --toc-depth=3 \
  --number-sections \
  --resource-path=. \
  -V lang=zh-CN
```

### 参数说明

| 参数 | 作用 |
|------|------|
| `cd /path/to/your/project` | 切换到 `outputs` 文件夹的父目录 |
| `pandoc outputs/final/report.md` | 指定输入的 Markdown 文件 |
| `-o outputs/final/report.docx` | 指定输出的 Word 文件 |
| `--toc` | 生成目录 |
| `--toc-depth=3` | 目录显示到三级标题 |
| `--number-sections` | 自动为章节标题编号 |
| `--resource-path=.` | 从当前目录（项目根目录）查找图片资源 |
| `-V lang=zh-CN` | 设置中文环境 |

### 路径解析原理

由于命令在项目根目录执行，且设置了 `--resource-path=.`，Pandoc 会将图片路径 `outputs/assets/charts/fig_1_1_xxx.png` 正确解析为：
- `./outputs/assets/charts/fig_1_1_xxx.png`（从项目根目录开始的完整路径）



## 强约束规则

- 必须先生成 `outputs/merged/abstracts.md`、`outputs/merged/body.md`、`outputs/merged/references.md`。
- 摘要必须整合生成，禁止简单拼接。
- 正文必须按章节顺序完整拼接。
- 参考文献必须去重并统一编号。
- `outputs/final/report.md` 必须由 `outputs/final/abstract.md`、`outputs/merged/body.md`、`outputs/final/refs.md` 拼接得到。
- 所有相对路径必须统一使用 `outputs/`。
- **执行 Word 转换时，必须位于 `outputs` 的父目录**，并使用 `--resource-path=.` 和 `-V lang=zh-CN` 参数。