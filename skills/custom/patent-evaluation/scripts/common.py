#!/usr/bin/env python3
"""专利评估脚本公共模块：ClickHouse 直连、SQL 拆分、结果格式化

通过 clickhouse-connect 直接连接 ClickHouse，无需依赖 MCP 工具。
连接参数从环境变量读取，默认值与 extensions_config.json 中的 mcp-clickhouse-hzq 配置一致。
"""

import asyncio
import os

from loguru import logger
import clickhouse_connect

# ── ClickHouse 连接参数 ────────────────────────────────────────────────
# 默认值与 extensions_config.json 中 mcp-clickhouse-hzq 的配置保持一致
CLICKHOUSE_HOST = os.environ.get("CLICKHOUSE_HOST", "dev.heidutech.cn")
CLICKHOUSE_PORT = int(os.environ.get("CLICKHOUSE_PORT", "31123"))
CLICKHOUSE_DATABASE = os.environ.get("CLICKHOUSE_DATABASE", "XiaoSu")
CLICKHOUSE_USER = os.environ.get("CLICKHOUSE_USER", "su")
CLICKHOUSE_PASSWORD = os.environ.get("CLICKHOUSE_PASSWORD", "s2026u")
CLICKHOUSE_SECURE = os.environ.get("CLICKHOUSE_SECURE", "false").lower() == "true"
CLICKHOUSE_CONNECT_TIMEOUT = int(os.environ.get("CLICKHOUSE_CONNECT_TIMEOUT", "30"))
CLICKHOUSE_SEND_RECEIVE_TIMEOUT = int(
    os.environ.get("CLICKHOUSE_SEND_RECEIVE_TIMEOUT", "3000")
)

# 模块级客户端缓存：延迟初始化，整个进程生命周期复用同一个连接
_client = None


def _get_client():
    """获取或创建 ClickHouse 客户端（延迟初始化 + 模块级缓存）"""
    global _client
    if _client is None:
        _client = clickhouse_connect.get_client(
            host=CLICKHOUSE_HOST,
            port=CLICKHOUSE_PORT,
            username=CLICKHOUSE_USER,
            password=CLICKHOUSE_PASSWORD,
            database=CLICKHOUSE_DATABASE,
            secure=CLICKHOUSE_SECURE,
            connect_timeout=CLICKHOUSE_CONNECT_TIMEOUT,
            send_receive_timeout=CLICKHOUSE_SEND_RECEIVE_TIMEOUT,
        )
        logger.info(
            f"ClickHouse 已连接: {CLICKHOUSE_HOST}:{CLICKHOUSE_PORT}/{CLICKHOUSE_DATABASE}"
        )
    return _client


async def execute_sql(sql: str):
    """执行单条 ClickHouse SQL

    使用 clickhouse-connect 同步客户端，通过 asyncio.to_thread 包装为异步，
    避免阻塞事件循环。查询和 DDL（CREATE/DROP/INSERT）均通过此函数执行。
    """
    client = _get_client()
    return await asyncio.to_thread(client.query, sql)


def split_sql_statements(sql_text: str) -> list:
    """按 ; 拆分 SQL 语句，正确处理字符串和注释内的分号。

    处理 ClickHouse SQL 中的：
    - 单引号字符串（支持 '' 转义）
    - 行注释 --
    - 块注释 /* */
    """
    statements = []
    buf = []
    i = 0
    n = len(sql_text)

    while i < n:
        ch = sql_text[i]

        # -- 行注释：一直读到行尾
        if ch == "-" and i + 1 < n and sql_text[i + 1] == "-":
            buf.append(ch)
            i += 1
            while i < n and sql_text[i] != "\n":
                buf.append(sql_text[i])
                i += 1
            continue

        # /* 块注释 */
        if ch == "/" and i + 1 < n and sql_text[i + 1] == "*":
            buf.append(ch)
            i += 1
            while i < n:
                buf.append(sql_text[i])
                if sql_text[i] == "*" and i + 1 < n and sql_text[i + 1] == "/":
                    i += 1
                    buf.append(sql_text[i])
                    break
                i += 1
            i += 1
            continue

        # 单引号字符串：处理 '' 转义
        if ch == "'":
            buf.append(ch)
            i += 1
            while i < n:
                buf.append(sql_text[i])
                if sql_text[i] == "'":
                    # 遇到引号，检查是否是转义 ''
                    if i + 1 < n and sql_text[i + 1] == "'":
                        buf.append("'")
                        i += 2
                        continue
                    # 字符串结束
                    i += 1
                    break
                i += 1
            continue

        # 语句分隔符（仅在字符串和注释外生效）
        if ch == ";":
            stmt = "".join(buf).strip()
            if stmt:
                statements.append(stmt)
            buf = []
            i += 1
            continue

        buf.append(ch)
        i += 1

    # 最后一条语句
    stmt = "".join(buf).strip()
    if stmt:
        statements.append(stmt)

    return statements


def format_result(result) -> str:
    """将 clickhouse-connect QueryResult 格式化为可读的表格字符串

    参数:
        result: clickhouse_connect.driver.QueryResult 对象，
                包含 .column_names (tuple) 和 .result_set (list of tuples)
    """
    try:
        columns = result.column_names
        rows = result.result_set
        if not rows:
            return "(空结果)"
        if len(rows) == 1:
            return " | ".join(f"{c}={v}" for c, v in zip(columns, rows[0]))
        widths = [
            max(len(str(c)), max((len(str(r[i])) for r in rows), default=0))
            for i, c in enumerate(columns)
        ]
        header = " | ".join(c.ljust(w) for c, w in zip(columns, widths))
        sep = "-+-".join("-" * w for w in widths)
        body = "\n".join(
            " | ".join(str(v).ljust(w) for v, w in zip(row, widths)) for row in rows
        )
        return f"\n{header}\n{sep}\n{body}"
    except Exception:
        pass
    return str(result)[:100]


async def execute_sql_file(label: str, filepath: str):
    """读取 SQL 文件并按分号拆分逐条执行

    参数:
        label: 日志标签（如 "Step1"）
        filepath: SQL 文件的绝对路径
    """
    with open(filepath, encoding="utf-8") as f:
        raw = f.read()

    statements = split_sql_statements(raw)
    # 过滤纯注释块
    statements = [
        s
        for s in statements
        if not all(
            l_str.strip().startswith("--") or l_str.strip() == ""
            for l_str in s.split("\n")
        )
    ]

    total = len(statements)
    logger.info(f"[{label}] 共 {total} 条 SQL 语句待执行")
    for i, stmt in enumerate(statements, 1):
        logger.info(f"[{label}] 执行第 {i}/{total} 条...")
        try:
            result = await execute_sql(stmt)
            logger.info(f"  完成: {format_result(result)}")
        except Exception as e:
            logger.exception(f"  错误: {e}")
            raise
