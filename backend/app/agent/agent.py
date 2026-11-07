import json
from mcp import Client
from app.agent.llm_client import client
from app.agent.prompts import build_system_prompt
from app.mcp.server import mcp
from app.agent.config import MAX_STEPS, FINAL_ANSWER
from app.agent.logging_utils import (
    _preview,    
    _tool_message_payload,
    _summarize_tool_result
)

async def run_agent(user_message: str, cv_text: str | None = None, history: list[dict] | None = None):
    """
    Args:
        user_message: The user's instructions. Can be a generic prompt like "find jobs that
            match my CV" when only the cv_text is provided.
        cv_text: Plain text extracted from the user's CV.
        history: The conversation history.
    """   

    async with Client(mcp) as mcp_client:

        # Get tools from MCP
        tools_result = await mcp_client.list_tools()

        tools = []

        for tool in tools_result.tools:
            tools.append(
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema,
                    },
                }
            )

        # Message history: one system message (tool guidance, plus the CV if
        # given) followed by the user's message. The agent then responds with
        # tool calls or a final answer.
        messages: list[dict] = [
        {"role": "system", "content": build_system_prompt(cv_text)},
        *(history or []),
        {"role": "user", "content": user_message},
    ]
        # Agent loop 
        for step in range(MAX_STEPS):
            last_step = step == MAX_STEPS - 1

            if last_step:
                messages.append({"role": "user", "content": FINAL_ANSWER})

            response = await client.generate(
                messages=messages,
                tools=tools,
                tool_choice="none" if last_step else "auto",
            )
            
            messages.append(
                {
                    "role": "assistant",
                    "content": response.content,
                    "tool_calls": [
                        tool_call.to_message_dict()
                        for tool_call in response.tool_calls
                    ],
                }
            )
            # On the last step we always return, even if the model ignored
            # tool_choice="none" and asked for another tool call.
            if not response.tool_calls or last_step:
                answer = response.content or (
                    "I couldn't finish the search. Please try again."
                )
                print("\nLLM summary:")
                print(answer)
                return answer

            for tool_call in response.tool_calls:

                function_name = tool_call.name
                arguments_dict = tool_call.arguments
                print(f"\n→ {function_name}({_preview(arguments_dict, 150)})")

                result = await mcp_client.call_tool(
                    function_name,
                    arguments_dict,
                )

                print(f"  {_summarize_tool_result(result)}")

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(
                            _tool_message_payload(result),
                            ensure_ascii=False,
                        ),
                    }
                )

        raise RuntimeError(f"Agent did not finish within {MAX_STEPS} steps")