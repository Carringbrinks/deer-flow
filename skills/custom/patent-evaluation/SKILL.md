---
name: patent-evaluation
description: >
  企业专利成果综合评价技能——对一批企业的专利数据进行深度调查、多维度评分和行业排名。

  【必触发规则】用户只要表达了以下意图之一，必须立即激活此技能，不得反问"哪些企业"或要求用户提供企业名单：
  - "专利成果数据" + 任何评价/分析/调查/排名/评估类词汇
  - "这批企业" / "这些企业" / "几家企业" / "一些企业" + "专利" 
  - "企业专利" + "调查/分析/评价/评估/排名/对比/实力/能力/成果"
  - "科创属性" / "专利实力" / "专利质量" / "专利布局" / "技术实力" + 企业
  - "行业排名" / "行业位阶" / "行业地位" / "行业对比" + 专利
  - 任何要求对企业做专利方面的综合分析、深度调查、成果评价的请求
  - 用户提供了企业名称列表并要求分析其专利情况

  【禁止反问】本技能的数据源已包含企业专利数据（patent_data_ccb 和 t_patent_data_ai 表），无需用户单独提供企业名单。
  即使用户未明确列出企业名称，也应直接运行分析流程，从数据库中获取结果。
  用户说"这批企业"时，指的是数据库中已有的企业数据，直接启动 run_all.py 即可。

  【三阶段流程】行业基准模型 → 企业科创属性评分 → 行业位阶排名。
  命令: cd skills/custom/patent-evaluation/scripts && python run_all.py
---

# 企业专利成果深度调查与综合评价

## 概述

本技能对专利数据进行系统性的**企业科创属性评价**和**行业位阶分析**，结合二者形成对企业专利实力的综合评价。分为三个阶段：

| 阶段 | 脚本 | 说明 |
|------|------|------|
| 第一阶段 | step1_industry_benchmark.py | 构建全球和中国行业基准 |
| 第二阶段 | step2_enterprise_eval.py | 企业多维度科创属性评分（CCB + AI） |
| 第三阶段 | step3_industry_rank.py | 计算企业行业位阶排名（CCB + AI） |

三个阶段必须按顺序执行：先建基准 → 再评价企业科创属性 → 最后算行业位阶，综合二者得出企业在行业中的定位。

## 快速开始

一键执行：
```bash
cd /mnt/skills/custom/patent-evaluation/scripts && python3 run_all.py
```

分步执行：分别运行 step1_industry_benchmark.py, step2_enterprise_eval.py, step3_industry_rank.py。

### 沙箱环境说明

本技能运行在 AIO Sandbox 容器中：

环境变量已预配置：
- `CLICKHOUSE_HOST=dev.heidutech.cn`
- `CLICKHOUSE_PORT=31123`
- `CLICKHOUSE_DATABASE=XiaoSu`
- `CLICKHOUSE_USER=su`
- `CLICKHOUSE_PASSWORD=s2026u`

**依赖要求**：沙箱中必须安装 `clickhouse-connect`、`loguru`：
```bash
pip install clickhouse-connect loguru
```

如遇 `import clickhouse_connect`、`import loguru` 失败，先验证：
```bash
python3 -c "import clickhouse_connect; import loguru; print('OK: clickhouse-connect and loguru available')"
```

## 数据库说明

所有脚本通过 `clickhouse-connect` 直接连接 ClickHouse，无需 MCP 工具。连接参数从环境变量读取，默认值与 `extensions_config.json` 中 `mcp-clickhouse-hzq` 的配置一致。

核心调用模式（`common.py` 封装）：
```python
import clickhouse_connect
client = clickhouse_connect.get_client(
    host="dev.heidutech.cn", port=31123,
    username="su", password="s2026u",
    database="XiaoSu",
)
result = client.query("SELECT ...")
# result.column_names → ('col1', 'col2', ...)
# result.result_set  → [('val1', 'val2'), ...]
```

| 表名 | 用途 |
|------|------|
| `XiaoSu.t_patent_data` | 全球专利数据（行业基准用） |
| `XiaoSu.patent_data_ccb` | 建行浙江企业专利数据（企业评价用，默认数据源） |
| `XiaoSu.t_patent_data_ai` | AI 企业专利数据（企业评价用，字段与计算逻辑与 patent_data_ccb 完全相同） |
| `XiaoSu.industry_quantile` | 输出：行业基准分位数 |
| `XiaoSu.enterprise_eval_result` | 输出：CCB 企业科创属性评价结果 |
| `XiaoSu.enterprise_eval_result_ai` | 输出：AI 企业科创属性评价结果（字段与 CCB 完全一致） |
| `XiaoSu.enterprise_industry_rank` | 输出：CCB 企业行业位阶排名 |
| `XiaoSu.enterprise_industry_rank_ai` | 输出：AI 企业行业位阶排名（字段与 CCB 完全一致） |

临时表以 `tmp_` 开头，每次运行会自动清理重建。

## 评价体系详解

### 第一阶段：行业基准（step1_industry_benchmark.py）

对每个 IPC 小类（前4位），分 `global` 和 `china` 两个范围，计算五维99分位数：

| 维度 | 说明 |
|------|------|
| density_dist | 企业在该小类的专利数量分布 |
| cited_dist | 专利被引用次数分布 |
| family_dist | 同族专利数分布 |
| claims_dist | 权利要求数分布 |
| value_dist | 专利价值评分分布 |

参考 SQL: `references/industry_benchmark_optimized.sql`

### 第二阶段：企业科创属性评价（step2_enterprise_eval.py）

依次处理 `patent_data_ccb` 和 `t_patent_data_ai` 两张表，7 维度加权评分（各维度 0-100 分）：

| 维度 | 权重 | 指标 |
|------|------|------|
| 数量实力 | 15% | 专利密度、类型多样性 |
| 质量水平 | 20% | 被引次数、权利要求数、同族数 |
| 布局广度 | 15% | IPC覆盖、战略性新兴产业、数字经济、绿色低碳 |
| 商业价值 | 15% | 转让、许可、质押次数 |
| 研发能力 | 10% | 发明人规模、申请人规模 |
| 法律状态 | 10% | 有效专利占比、复审无效诉讼风险 |
| 资质属性 | 15% | 科技型/高新技术企业、上市状态、企业规模 |

参考 SQL: `references/enterprise_eval_ch.sql`（CCB）、`references/enterprise_eval_ai.sql`（AI）

### 第三阶段：行业位阶（step3_industry_rank.py）

依次处理 CCB 和 AI 企业的临时表数据，**结合企业科创属性评分和行业基准**，计算行业位阶排名：

1. 取每家企业专利数量最多的前3个IPC小类
2. 对照 `industry_quantile` 分位数插值得到百分位
3. 按专利数量加权计算三维综合百分位
4. 结合科创属性评分和行业位阶百分位，按综合百分位分档：

| 百分位 | 档位 |
|--------|------|
| ≥ 90 | 行业领先 |
| ≥ 70 | 行业优秀 |
| ≥ 50 | 行业中上 |
| ≥ 30 | 行业平均 |
| ≥ 10 | 行业落后 |
| < 10 | 行业底部 |

参考 SQL: `references/enterprise_industry_rank_v3.sql`（CCB）、`references/enterprise_industry_rank_ai.sql`（AI）

## 用户交互指引

| 用户问法（自然语言） | 执行动作 | 说明 |
|----------------------|----------|------|
| 深度调查这批企业的专利成果数据并做出综合评价 | 运行 `run_all.py` 全流程 | 自动处理 CCB + AI 两张表 |
| 分析这些企业的专利情况 | 运行 `run_all.py` 全流程 | 企业名单已在数据库中 |
| 帮我看看这几家公司的专利实力怎么样 | 运行 `run_all.py` 全流程 | 直接执行，无需确认企业 |
| 做一次企业专利成果深度调查 | 运行 `run_all.py` 全流程 | CCB 和 AI 数据一并评价 |
| 评估企业科创属性和行业地位 | 运行 `run_all.py` 全流程 | — |
| 这批企业的行业排名如何 | 运行 `run_all.py` 全流程 | — |
| 查看行业基准数据 | 运行 step1 后查询 `industry_quantile` | 仅需基准数据时 |
| 只看企业科创属性评分 | 运行 step2 后查询 `enterprise_eval_result` | 已有基准数据时 |
| 只看行业位阶排名 | 运行 step3 后查询 `enterprise_industry_rank` | 已有评价结果时 |
| 重新计算/更新结果 | 运行 `run_all.py` | 自动清理旧表 |



## 注意事项

1. 所有 SQL 通过 `clickhouse-connect` 直接连接 ClickHouse 执行，无需 MCP 工具
2. 运行前确保 ClickHouse 服务可用（`dev.heidutech.cn:31123`）且网络可达
3. 每次运行自动清理临时表
4. 第一阶段数据量大，耗时较长
5. 参考 SQL 在 `references/` 目录
6. **用户说"这批企业"/"这些企业"时，指的是数据库 `patent_data_ccb` 和 `t_patent_data_ai` 两张表中已有的企业，不是要求用户提供名单**
7. **每次运行自动处理两张表：patent_data_ccb（建行浙江）和 t_patent_data_ai（AI 数据），计算逻辑完全一致，临时表通过 `_ai` 后缀区分**
8. **切勿反问用户"请问您要分析哪些企业"或"请提供企业名单"——直接运行分析即可**
9. 如果报告中需要绘图，必须在沙箱中安装中文字体，否则图表中的中文会显示为乱码。安装方法：
```bash
apt-get update && apt-get install -y fonts-noto-cjk fonts-wqy-microhei
```
