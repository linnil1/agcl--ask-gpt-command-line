from dataclasses import dataclass
from enum import StrEnum, auto
from typing import Any
import json

from loguru import logger
from openai import AsyncOpenAI
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam

from interact import get_openai_key

# client = AsyncOpenAI(api_key=ConfigManager().get("openai_key"))
client = None


class SuggestionType(StrEnum):
    ASK = auto()
    FIX = auto()


PROMPT_ASK = """
You are a knowledgeable assistant that helps users by
suggesting the most appropriate command-line commands based on their input.
When a user describes a task they want to accomplish,
provide a list of potential command-line commands that can help them achieve that task.
Be specific and ensure that the commands are relevant and commonly used for the described task.
Include options and flags that might be useful.
If the provided information is insufficient to diagnose the issue,
suggest a command to gather the necessary information before providing a final recommendation.
""".strip()

PROMPT_FIX = """
You are a helpful assistant that provides command-line command suggestions to
troubleshoot and fix problems based on the user's history
of inputs and the most recent output and error messages. 
When given a user's command history and the latest output and error messages,
analyze the situation and provide specific command-line commands that can resolve the issue. 
If the user's command is correct and no issues are found,
explain why the command is correct and no further action is needed.
If the provided information is insufficient to diagnose the issue,
suggest a command to gather the necessary inormation before providing a final recommendation,
result of the command will be used in the next interaction.
""".strip()
# If the user has previously rejected some commands, avoid suggesting those commands again.


FUNC_CMD = """
A valid command-line command that can be executed to resolve the issue.
If more information is needed to diagnose the issue,
also suggest a valid command-line command to gather the necessary information.
Leave empty list if nothing to do.
""".strip()

FUNC_DESCR = """
A brief explanation of what the command does and why it helps,
or confirmation that the command is correct and no further action is needed.
""".strip()


@dataclass
class UserInput:
    suggestion_type: SuggestionType = SuggestionType.ASK
    text: str = ""
    last_message: str = ""

    def create_message(self) -> list[ChatCompletionMessageParam]:
        if self.suggestion_type == SuggestionType.ASK:
            messages: list[ChatCompletionMessageParam] = [
                {
                    "role": "system",
                    "content": PROMPT_ASK,
                },
                {"role": "user", "content": self.text},
            ]
        elif self.suggestion_type == SuggestionType.FIX:
            messages = [
                {"role": "system", "content": PROMPT_FIX},
                {"role": "user", "content": self.last_message},
            ]
        return messages


@dataclass
class Suggestion:
    description: str
    commands: list[str]
    last_message: Any = None


async def get_gpt_suggestions(
    messages: list[ChatCompletionMessageParam], model: str
) -> Suggestion:
    global client
    if client is None:
        client = AsyncOpenAI(api_key=get_openai_key())

    logger.debug(messages)
    response = await client.chat.completions.create(
        model=model,
        messages=messages,
        # tool_choice="required",
        tools=[
            {
                "type": "function",
                "function": {
                    "name": "recommend_command_line",
                    "description": "Recommends command-line commands based on user input.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "recommendations": {
                                "type": "array",
                                "items": {"type": "string", "description": FUNC_CMD},
                            },
                            "description": {
                                "type": "string",
                                "description": FUNC_DESCR,
                            },
                        },
                    },
                },
            }
        ],
    )
    message = response.choices[0].message
    logger.debug(response)
    if not message.tool_calls:
        return Suggestion(
            description=message.content or "",
            commands=[],
        )

    data = json.loads(message.tool_calls[0].function.arguments)
    if not data:
        raise ValueError("GPT give empty result")

    return Suggestion(
        description=data.get("description", ""),
        commands=data["recommendations"],
        last_message=message,
    )


def create_exclude_command_message(commands: list[str]) -> ChatCompletionMessageParam:
    return {
        "role": "user",
        "content": "Below command are not valid or not wanted by user:\n"
        + "\n".join(map(lambda i: "* " + i, commands)),
    }
