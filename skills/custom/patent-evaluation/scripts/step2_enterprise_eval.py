#!/usr/bin/env python3
"""第二阶段：企业科创属性评价
依次基于 patent_data_ccb（建行浙江专利数据）和 t_patent_data_ai（AI 专利数据），
按 7 个维度对企业进行综合评分。
输出表：XiaoSu.enterprise_eval_result（CCB）、XiaoSu.enterprise_eval_result_ai（AI）
依赖 SQL：../references/enterprise_eval_ch.sql、../references/enterprise_eval_ai.sql
阶段依赖：需要先执行 step1（行业基准），但本脚本独立于 step1 运行。
"""

import asyncio
import os
import sys

from loguru import logger

from common import execute_sql, execute_sql_file, format_result

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SQL_REF_DIR = os.path.join(SKILL_DIR, "references")

LABEL = "Step2"


async def main():
    # ── CCB 数据源 ────────────────────────────────────────────────
    sql_file_ccb = os.path.join(SQL_REF_DIR, "enterprise_eval_ch.sql")
    if not os.path.exists(sql_file_ccb):
        logger.error(f"找不到 SQL 文件 {sql_file_ccb}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("第二阶段：企业科创属性评价")
    logger.info("=" * 60)

    # ── 清理所有临时表（CCB + AI）────────────────────────────────
    logger.info(f"[{LABEL}] 清理历史临时表...")
    cleanup_sqls = [
        "DROP TABLE IF EXISTS XiaoSu.tmp_enterprise_patent",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ipc_classes",
        "DROP TABLE IF EXISTS XiaoSu.tmp_strategic",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ipc_count",
        "DROP TABLE IF EXISTS XiaoSu.tmp_strategic_count",
        "DROP TABLE IF EXISTS XiaoSu.tmp_enterprise_patent_ai",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ipc_classes_ai",
        "DROP TABLE IF EXISTS XiaoSu.tmp_strategic_ai",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ipc_count_ai",
        "DROP TABLE IF EXISTS XiaoSu.tmp_strategic_count_ai",
    ]
    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
        except Exception:
            pass

    # ── 1) CCB 数据 ──────────────────────────────────────────────
    logger.info(f"[{LABEL}] >>> 执行 CCB 数据评价（patent_data_ccb）...")
    await execute_sql_file(f"{LABEL}-CCB", sql_file_ccb)

    # ── 2) AI 数据 ───────────────────────────────────────────────
    sql_file_ai = os.path.join(SQL_REF_DIR, "enterprise_eval_ai.sql")
    if not os.path.exists(sql_file_ai):
        logger.error(f"找不到 SQL 文件 {sql_file_ai}")
        sys.exit(1)

    logger.info(f"[{LABEL}] >>> 执行 AI 数据评价（t_patent_data_ai）...")
    await execute_sql_file(f"{LABEL}-AI", sql_file_ai)

    # ── 验证结果 ─────────────────────────────────────────────────
    logger.info(f"[{LABEL}] 验证结果...")
    result = await execute_sql(
        "SELECT count() AS enterprise_count, "
        "round(avg(total_score), 2) AS avg_score, "
        "round(max(total_score), 2) AS max_score "
        "FROM XiaoSu.enterprise_eval_result"
    )
    logger.info(f"enterprise_eval_result (CCB): {format_result(result)}")

    result_ai = await execute_sql(
        "SELECT count() AS enterprise_count, "
        "round(avg(total_score), 2) AS avg_score, "
        "round(max(total_score), 2) AS max_score "
        "FROM XiaoSu.enterprise_eval_result_ai"
    )
    logger.info(f"enterprise_eval_result_ai (AI): {format_result(result_ai)}")

    logger.info("第二阶段完成！")


if __name__ == "__main__":
    asyncio.run(main())
