#!/usr/bin/env python3
"""第一阶段：行业基准构建
基于全球专利数据，按 IPC 小类（前4位）计算全球和中国两个范围的五维99分位数基准。
输出表：XiaoSu.industry_quantile
依赖 SQL：../references/industry_benchmark_optimized.sql
"""

import asyncio
import os
import sys

from loguru import logger

from common import execute_sql, execute_sql_file, format_result

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SQL_REF_DIR = os.path.join(SKILL_DIR, "references")

LABEL = "Step1"


async def main():
    sql_file = os.path.join(SQL_REF_DIR, "industry_benchmark_optimized.sql")
    if not os.path.exists(sql_file):
        logger.error(f"找不到 SQL 文件 {sql_file}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info("第一阶段：行业基准计算")
    logger.info(f"SQL 文件: {sql_file}")
    logger.info("=" * 60)

    logger.info(f"[{LABEL}] 清理历史临时表...")
    cleanup_sqls = [
        "DROP TABLE IF EXISTS XiaoSu.tmp_patent_dedup",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_global",
        "DROP TABLE IF EXISTS XiaoSu.tmp_ent_subclass_china",
    ]
    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
        except Exception:
            pass

    await execute_sql_file(LABEL, sql_file)

    logger.info(f"[{LABEL}] 验证结果...")
    result = await execute_sql(
        "SELECT scope, count() AS cnt FROM XiaoSu.industry_quantile GROUP BY scope ORDER BY scope"
    )
    logger.info(f"industry_quantile 行数: {format_result(result)}")

    logger.info("第一阶段完成！")


if __name__ == "__main__":
    asyncio.run(main())
