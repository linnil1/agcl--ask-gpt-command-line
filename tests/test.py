import pytest
import asyncio

from config import ConfigManager
import history
from history import read_last_log, execute_command
from suggest import (
    SuggestionType,
    UserInput,
    create_exclude_command_message,
    get_gpt_suggestions,
)


@pytest.mark.asyncio
async def test_run():
    command = "echo 123".split(" ")
    await execute_command(" ".join(command))
    with open(ConfigManager().get_log_file()) as f:
        assert f.read().endswith("Message:\n123\n")


@pytest.mark.asyncio
async def test_ask():
    prompt = "list file in this dir".split(" ")
    user_input = UserInput(
        SuggestionType.ASK,
        text=" ".join(prompt),
    )
    messages = user_input.create_message()
    not_wanted_commands = ["dir"]
    if not_wanted_commands:
        messages.append(create_exclude_command_message(not_wanted_commands))
    suggestion = await get_gpt_suggestions(messages, "gpt-3.5-turbo")
    flag_ok = False
    for cmd in suggestion.commands:
        if cmd.startswith("ls"):
            flag_ok = True
            break
    assert flag_ok


@pytest.mark.asyncio
async def test_fix():
    user_input = UserInput(
        SuggestionType.FIX,
        last_message="""
$ l s -alh
ls: cannot access 's': No such file or directory
""",
    )
    messages = user_input.create_message()
    suggestion = await get_gpt_suggestions(messages, "gpt-3.5-turbo")
    flag_ok = False
    for cmd in suggestion.commands:
        if cmd.startswith("ls"):
            flag_ok = True
            break
    assert flag_ok


@pytest.mark.asyncio
async def test_command_line():
    process = await asyncio.create_subprocess_shell("agcl run ls")
    await process.communicate()
    assert process.returncode == 0


@pytest.mark.asyncio
async def test_last_log(monkeypatch):
    with open("/tmp/tmp_agcl_history", "w") as file:
        file.write("echo 123\npytest")
    monkeypatch.setattr(history, "get_history_file", lambda _: "/tmp/tmp_agcl_history")

    log = await read_last_log()
    assert log.endswith("123\n")
