#!/usr/bin/env python3
"""第三阶段：企业行业位阶排名
依次取 CCB 和 AI 企业专利数量最多的前 3 个 IPC 小类，对照行业基准分位数插值得出百分位，
按专利数量加权计算综合百分位并分档定级。
输出表：XiaoSu.enterprise_industry_rank（CCB）、XiaoSu.enterprise_industry_rank_ai（AI）
依赖 SQL：../references/enterprise_industry_rank_v3.sql、../references/enterprise_industry_rank_ai.sql
阶段依赖：需要先执行 step1 和 step2。
"""

import asyncio
import os
import sys

from loguru import logger

from common import execute_sql, execute_sql_file, format_result

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SQL_REF_DIR = os.path.join(SKILL_DIR, "references")

LABEL = "Step3"


async def main():
    # ── CCB 数据源 ────────────────────────────────────────────────
    sql_file_ccb = os.path.join(SQL_REF_DIR, "enterprise_industry_rank_v3.sql")
    if not os.path.exists(sql_file_ccb):
        logger.error(f"找不到 SQL 文件 {sql_file_ccb}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("第三阶段：企业行业位阶排名")
    logger.info("=" * 60)

    # ── 清理所有临时表（CCB + AI）────────────────────────────────
    logger.info(f"[{LABEL}] 清理历史临时表...")
    cleanup_sqls = [
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_metrics_ai",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_top3_subclass_ai",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_pct_ai",
    ]
    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
        except Exception:
            pass

    # ── 1) CCB 数据 ──────────────────────────────────────────────
    logger.info(f"[{LABEL}] >>> 执行 CCB 数据排名（tmp_enterprise_patent）...")
    await execute_sql_file(f"{LABEL}-CCB", sql_file_ccb)

    # ── 2) AI 数据 ───────────────────────────────────────────────
    sql_file_ai = os.path.join(SQL_REF_DIR, "enterprise_industry_rank_ai.sql")
    if not os.path.exists(sql_file_ai):
        logger.error(f"找不到 SQL 文件 {sql_file_ai}")
        sys.exit(1)

    logger.info(f"[{LABEL}] >>> 执行 AI 数据排名（tmp_enterprise_patent_ai）...")
    await execute_sql_file(f"{LABEL}-AI", sql_file_ai)

    # ── 验证结果 ─────────────────────────────────────────────────
    logger.info(f"[{LABEL}] 验证结果...")
    result = await execute_sql(
        "SELECT level, count() AS cnt FROM XiaoSu.enterprise_industry_rank "
        "GROUP BY level ORDER BY cnt DESC"
    )
    logger.info(f"enterprise_industry_rank (CCB) 等级分布: {format_result(result)}")

    result_ai = await execute_sql(
        "SELECT level, count() AS cnt FROM XiaoSu.enterprise_industry_rank_ai "
        "GROUP BY level ORDER BY cnt DESC"
    )
    logger.info(
        f"enterprise_industry_rank_ai (AI) 等级分布: {format_result(result_ai)}"
    )

    logger.info("第三阶段完成！")


if __name__ == "__main__":
    asyncio.run(main())
