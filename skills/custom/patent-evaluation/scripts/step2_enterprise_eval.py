#!/usr/bin/env python3
"""第二阶段：企业科创属性评价
基于指定的企业专利数据表，按 7 个维度对企业进行综合评分。
由 run_all.py 调用，参数通过 --datasets 指定。

输出表：XiaoSu.enterprise_eval_result{suffix}
SQL 模板：../references/enterprise_eval_template.sql
"""

import asyncio
import os
import sys

from loguru import logger

from common import execute_sql, execute_sql_text, format_result, render_sql_template

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)
SQL_REF_DIR = os.path.join(SKILL_DIR, "references")

LABEL = "Step2"


async def main(source_table: str, suffix: str):
    template_file = os.path.join(SQL_REF_DIR, "enterprise_eval_template.sql")
    if not os.path.exists(template_file):
        logger.error(f"找不到 SQL 模板文件 {template_file}")
        sys.exit(1)

    logger.info("=" * 60)
    logger.info(f"第二阶段：企业科创属性评价（{source_table} → suffix={suffix!r}）")
    logger.info("=" * 60)

    # 清理临时表
    logger.info(f"[{LABEL}] 清理历史临时表...")
    cleanup_sqls = [
        f"DROP TABLE IF EXISTS XiaoSu.tmp_enterprise_patent{suffix}",
        f"DROP TABLE IF EXISTS XiaoSu.tmp_ipc_classes{suffix}",
        f"DROP TABLE IF EXISTS XiaoSu.tmp_strategic{suffix}",
        f"DROP TABLE IF EXISTS XiaoSu.tmp_ipc_count{suffix}",
        f"DROP TABLE IF EXISTS XiaoSu.tmp_strategic_count{suffix}",
    ]
    for sql in cleanup_sqls:
        try:
            await execute_sql(sql)
        except Exception:
            pass

    # 渲染并执行模板 SQL
    logger.info(f"[{LABEL}] 渲染并执行 SQL 模板...")
    rendered = render_sql_template(
        template_file, source_table=source_table, suffix=suffix
    )
    await execute_sql_text(LABEL, rendered)

    # 验证结果
    logger.info(f"[{LABEL}] 验证结果...")
    result = await execute_sql(
        f"SELECT count() AS enterprise_count, "
        f"round(avg(total_score), 2) AS avg_score, "
        f"round(max(total_score), 2) AS max_score "
        f"FROM XiaoSu.enterprise_eval_result{suffix}"
    )
    logger.info(f"enterprise_eval_result{suffix}: {format_result(result)}")
    logger.info(f"第二阶段完成！（{source_table}）")


if __name__ == "__main__":
    # 直接运行时从命令行读取参数
    import argparse
    parser = argparse.ArgumentParser(description="企业科创属性评价")
    parser.add_argument("--source-table", required=True, help="源表全路径")
    parser.add_argument("--suffix", required=True, help="表后缀")
    args, _ = parser.parse_known_args()
    asyncio.run(main(source_table=args.source_table, suffix=args.suffix))
