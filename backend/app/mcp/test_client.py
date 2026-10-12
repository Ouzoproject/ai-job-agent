import asyncio

from mcp import Client

from app.mcp.server import mcp

async def main():
    async with Client(mcp) as client:
        print("Connected to MCP server.")

        print("\nAvailable tools:")

        tools = await client.list_tools()
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")

        print("\nCalling search_jobs...")

        result = await client.call_tool(
            "search_jobs", 
            {"query": "Machine Learning", "location": "Hamburg",}
        )

        print("\nResult:")
        print(result)

if __name__ == "__main__":
    asyncio.run(main())