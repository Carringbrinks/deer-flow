import asyncio

from deerflow.mcp.tools import get_mcp_tools

DEER_FLOW_EXTENSIONS_CONFIG_PATH = "/data2/deer-flow/extensions_config.json"


async def main():
    tools = await get_mcp_tools()
    print("TOOL_COUNT", len(tools))
    for t in tools:
        print(t.name)

    run = next(t for t in tools if t.name == "mcp-clickhouse-hzq_run_query")
    result = await run.ainvoke({"query": "SELECT currentDatabase() AS db"})
    print("QUERY_RESULT", result)
    result = await run.ainvoke({"query": "SHOW TABLES"})
    print(result)
    result = await run.ainvoke({"query": "SELECT * FROM distributed_CNKI LIMIT 1"})
    print(result)
    result = await run.ainvoke({"query": "SHOW CREATE TABLE distributed_CNKI"})
    print(result)
    result = await run.ainvoke(
        {
            "query": """
    SELECT
        title,
        creator,
        journal,
        year
    FROM distributed_CNKI
    LIMIT 5
    """
        }
    )
    print(result)


asyncio.run(main())
