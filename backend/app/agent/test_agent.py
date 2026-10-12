import asyncio
from app.agent.agent import run_agent


async def main():
    prompt = "Search for a position in data, ideally in data engineering or as data scientist in Berlin"
    try:
        result = await run_agent(prompt)
        print(f"Agent response:\n{result}")
    except Exception as exc: 
        print(f"ERROR while running this prompt: {exc!r}")


if __name__ == "__main__":
    asyncio.run(main())