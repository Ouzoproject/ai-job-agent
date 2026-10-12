import json
import os
from dataclasses import dataclass
from typing import cast

from dotenv import load_dotenv
from openai import AsyncOpenAI
from openai.types.chat import (
    ChatCompletionMessageParam,
    ChatCompletionToolChoiceOptionParam,
    ChatCompletionToolUnionParam,
)

from app.agent.config import MODEL

load_dotenv()

from dataclasses import dataclass


@dataclass
class ToolCall:
    id: str
    name: str
    arguments: dict

    def to_message_dict(self) -> dict:
        return {
            "id": self.id,
            "type": "function",
            "function": {
                "name": self.name,
                "arguments": json.dumps(self.arguments),
            },
        }

@dataclass
class LLMResponse:
    content: str | None
    tool_calls: list[ToolCall]

class LLMClient:

    def __init__(self):
        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("LLM_API_KEY"),
        )

    async def generate(
        self,
        messages: list[dict],
        tools: list[dict],
        tool_choice: str,
    ) -> LLMResponse:

        response = await self.client.chat.completions.create(
            model=MODEL,
            messages=cast(list[ChatCompletionMessageParam], messages),
            tools=cast(list[ChatCompletionToolUnionParam], tools),
            tool_choice=cast(ChatCompletionToolChoiceOptionParam, tool_choice),
        )

        if not response or not response.choices:
            raise RuntimeError(
                f"LLM returned an invalid response: {response}"
            )

        message = response.choices[0].message

        tool_calls = []

        for call in message.tool_calls or []:

            if call.type != "function":
                continue

            tool_calls.append(
                ToolCall(
                    id=call.id,
                    name=call.function.name,
                    arguments=json.loads(call.function.arguments),
                )
            )

        return LLMResponse(
            content=message.content,
            tool_calls=tool_calls,
        )


client = LLMClient()