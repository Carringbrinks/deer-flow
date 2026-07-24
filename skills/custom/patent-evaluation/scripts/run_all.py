#!/usr/bin/env python3
"""
一键编排脚本：依次执行三个阶段，支持通过 --datasets 指定数据源。
运行顺序：step1 (行业基准) -> step2 (企业评价, 每表) -> step3 (行业位阶, 每表)

用法：
  python run_all.py --datasets patent_data_ccb:ccb,t_patent_data_ai:ai
  python run_all.py --datasets patent_data_ccb:ccb            # 单表
  python run_all.py --datasets my_table:my_label              # 自定义表
  python run_all.py --datasets patent_data_ccb                # 无 suffix，自动推导为 _ccb

datasets 格式:
  table_name[:suffix],table_name[:suffix],...
  - table_name: 源表名（不含 XiaoSu. 前缀也可，脚本自动补全）
  - suffix: 可选，用于命名临时表和结果表。省略时从表名自动推导
    推导规则: 去掉 XiaoSu. 前缀 → 去掉 patent_data_ / t_patent_data_ 前缀 → 余下部分作 suffix
    例: patent_data_ccb → _ccb, t_patent_data_ai → _ai, my_data → _my_data
"""

import asyncio
import os

from loguru import logger

from common import execute_sql, format_result

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_datasets(raw: str) -> list[tuple[str, str]]:
    """解析 --datasets 参数为 (source_table, suffix) 列表。

    格式: table_name[:suffix],table_name[:suffix],...
    例: "patent_data_ccb:ccb,t_patent_data_ai:ai"
    """
    datasets = []
    for item in raw.split(","):
        item = item.strip()
        if not item:
            continue
        parts = item.split(":", 1)
        table_name = parts[0].strip()

        # 自动补全 XiaoSu. 前缀
        if "." not in table_name:
            table_name = f"XiaoSu.{table_name}"

        if len(parts) == 2 and parts[1].strip():
            suffix = f"_{parts[1].strip()}"
        else:
            suffix = _derive_suffix(table_name)

        datasets.append((table_name, suffix))
    return datasets


def _derive_suffix(table_name: str) -> str:
    """从表名自动推导 suffix。"""
    name = table_name.replace("XiaoSu.", "")
    for prefix in ["patent_data_", "t_patent_data_"]:
        if name.startswith(prefix):
            name = name[len(prefix):]
            break
    return f"_{name}"


async def cleanup_all(suffixes: list[str]):
    """清理所有临时表和历史结果表"""
    logger.info("=" * 60)
    logger.info("清理所有临时表和历史结果表...")
    logger.info("=" * 60)

    cleanup_sqls = [
        "DROP TABLE IF EXISTS XiaoSu.tmp_patent_dedup",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_global",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_china",
        "DROP TABLE IF EXISTS XiaoSu.industry_quantile",
    ]

    for suffix in suffixes:
        cleanup_sqls.extend([
            f"DROP TABLE IF EXISTS XiaoSu.tmp_enterprise_patent{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_ipc_classes{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_strategic{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_ipc_count{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_strategic_count{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.enterprise_eval_result{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct{suffix}",
            f"DROP TABLE IF EXISTS XiaoSu.enterprise_industry_rank{suffix}",
        ])

    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
            name = sql.split("IF EXISTS ")[-1]
            logger.info(f"  [OK] {name}")
        except Exception as e:
            name = sql.split("IF EXISTS ")[-1]
            logger.warning(f"  [FAIL] {name}: {e}")

    logger.info("清理完成!")
    logger.info("")


async def run_step(step_num: int, **kwargs):
    """动态加载并执行指定阶段的脚本，透传参数"""
    step_scripts = {
        1: ("step1_industry_benchmark.py", "行业基准构建"),
        2: ("step2_enterprise_eval.py", "企业科创属性评价"),
        3: ("step3_industry_rank.py", "企业行业位阶排名"),
    }

    script_name, desc = step_scripts[step_num]
    script_path = os.path.join(SCRIPT_DIR, script_name)

    logger.info("")
    logger.info("=" * 60)
    logger.info(f"> 开始执行第 {step_num} 阶段：{desc}")
    if kwargs:
        logger.info(f"  参数: {kwargs}")
    logger.info("=" * 60)

    import importlib.util

    spec = importlib.util.spec_from_file_location(f"step{step_num}", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    await module.main(**kwargs)


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="专利评价三阶段分析一键编排")
    parser.add_argument(
        "--datasets",
        type=str,
        required=True,
        help="数据集列表，格式: table[:suffix],table[:suffix],...",
    )
    args, _ = parser.parse_known_args()

    datasets = parse_datasets(args.datasets)
    suffixes = [s for _, s in datasets]

    logger.info("=" * 60)
    logger.info("专利数据分析一键编排")
    logger.info(f"数据源数量: {len(datasets)}")
    for src, suf in datasets:
        logger.info(f"  {src} → suffix={suf!r}")
    logger.info("运行顺序：行业基准 -> 企业评价 -> 行业位阶")
    logger.info("=" * 60)

    await cleanup_all(suffixes)

    # Step 1: 行业基准（仅一次，基于 t_patent_data）
    await run_step(1)

    # Step 2 + 3: 每个数据集
    for source_table, suffix in datasets:
        await run_step(2, source_table=source_table, suffix=suffix)
        await run_step(3, suffix=suffix)

    # 输出结果概览
    logger.info("")
    logger.info("=" * 60)
    logger.info("全部三阶段分析完成!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("结果概览：")
    for source_table, suffix in datasets:
        try:
            result = await execute_sql(
                f"SELECT level, count() AS cnt "
                f"FROM XiaoSu.enterprise_industry_rank{suffix} "
                f"GROUP BY level ORDER BY cnt DESC"
            )
            logger.info(f"{source_table}{suffix} 行业位阶分布：{format_result(result)}")
        except Exception as e:
            logger.error(f"无法查询 {source_table} 结果：{e}")


if __name__ == "__main__":
    asyncio.run(main())
