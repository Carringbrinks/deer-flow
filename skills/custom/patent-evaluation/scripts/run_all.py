#!/usr/bin/env python3
"""
一键编排脚本：依次执行三个阶段，并在开始时清理所有临时表和历史结果。
运行顺序：step1 (行业基准) -> step2 (企业评价) -> step3 (行业位阶)

用法：
  python run_all.py              # 全量运行（清除并重建）
  python run_all.py --step 1     # 只运行第一阶段
  python run_all.py --step 2     # 只运行第二阶段
  python run_all.py --step 3     # 只运行第三阶段
  python run_all.py --clean      # 仅清理所有表，不运行分析
"""

import asyncio
import os

from loguru import logger

from common import execute_sql, format_result

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


async def cleanup_all():
    """清理所有临时表和历史结果表"""
    logger.info("=" * 60)
    logger.info("全量清理所有临时表和历史结果表，开始重新计算...")
    logger.info("=" * 60)

    cleanup_sqls = [
        # Step1 临时表和结果表 (XiaoSu)
        "DROP TABLE IF EXISTS XiaoSu.tmp_patent_dedup",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_global",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_china",
        "DROP TABLE IF EXISTS XiaoSu.industry_quantile",
        # Step2 临时表和结果表 (XiaoSu)
        "DROP TABLE IF EXISTS XiaoSu.tmp_enterprise_patent",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ipc_classes",
        "DROP TABLE IF EXISTS XiaoSu.tmp_strategic",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ipc_count",
        "DROP TABLE IF EXISTS XiaoSu.tmp_strategic_count",
        "DROP TABLE IF EXISTS XiaoSu.enterprise_eval_result",
        # Step3 临时表和结果表 (XiaoSu)
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct",
        "DROP TABLE IF EXISTS XiaoSu.enterprise_industry_rank",
    ]

    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
            name = sql.split("IF EXISTS ")[-1]
            logger.info(f"  [OK] {name}")
        except Exception as e:
            name = sql.split("IF EXISTS ")[-1]
            logger.warning(f"  [FAIL] {name}: {e}")

    logger.info("全量清理完成!")
    logger.info("")


async def run_step(step_num: int):
    """动态加载并执行指定阶段的脚本"""
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
    logger.info("=" * 60)

    import importlib.util

    spec = importlib.util.spec_from_file_location(f"step{step_num}", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    await module.main()


async def main():
    import argparse

    parser = argparse.ArgumentParser(description="专利评价三阶段分析一键编排")
    parser.add_argument(
        "--step",
        type=int,
        choices=[1, 2, 3],
        help="只运行指定阶段 (1/2/3)，不指定则全量运行",
    )
    parser.add_argument("--clean", action="store_true", help="仅清理所有表，不运行分析")
    args, _ = parser.parse_known_args()

    if args.clean:
        await cleanup_all()
        return

    if args.step:
        # 单步运行
        await run_step(args.step)
    else:
        # 全量运行：清理 -> 三步顺序执行
        logger.info("=" * 60)
        logger.info("专利数据分析一键编排")
        logger.info("运行顺序：行业基准 -> 企业评价 -> 行业位阶")
        logger.info("=" * 60)

        await cleanup_all()
        await run_step(1)
        await run_step(2)
        await run_step(3)

        logger.info("")
        logger.info("=" * 60)
        logger.info("全部三阶段分析完成!")
        logger.info("=" * 60)

        # 输出结果概览
        logger.info("")
        logger.info("结果概览：")
        try:
            result = await execute_sql(
                "SELECT level, count() AS cnt FROM XiaoSu.enterprise_industry_rank "
                "GROUP BY level ORDER BY cnt DESC"
            )
            logger.info(f"行业位阶分布：{format_result(result)}")
        except Exception as e:
            logger.error(f"无法查询结果：{e}")


if __name__ == "__main__":
    asyncio.run(main())
