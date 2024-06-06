import asyncio
import os
import sys
from typing import AsyncIterator, TextIO

from loguru import logger
from config import ConfigManager, PROGRAM_NAME


async def get_last_command() -> str:
    process = await asyncio.create_subprocess_shell(
        # " ".join(['fc', '-ln', '-1']),
        f"zsh -c 'HISTFILE=~/.zsh_history fc -R  && fc -ln -1'",
        stdout=asyncio.subprocess.PIPE,
    )
    result, _ = await process.communicate()
    history_lines = result.decode().strip().split("\n")
    logger.debug(history_lines)
    return history_lines[-2]


async def read_last_log() -> str:
    last_command = await get_last_command()
    if not last_command.startswith(PROGRAM_NAME):
        logger.info(
            f"Last command is not from {PROGRAM_NAME}, run again to capture stdout/stderr"
            f"command = {last_command}"
        )
        await execute_command(last_command)

    logfile = ConfigManager().get_log_file()
    with open(logfile) as f:
        return f.read()


async def read_stream(
    stream: AsyncIterator[bytes], log: TextIO, stream_name: str
) -> None:
    screen = sys.stdout if stream_name == "stdout" else sys.stderr
    while True:
        line = await stream.readline()
        if not line:
            break
        decoded_line = line.decode()
        screen.write(decoded_line)
        log.write(decoded_line)


async def execute_command(command: str) -> None:
    logfile = ConfigManager().get_log_file()

    with open(logfile, "w") as log:
        log.write(f"Current Directory: {os.getcwd()}\n")
        log.write(f"Current User: {os.getlogin()}\n")
        log.write(f"Command: {command}\n")
        log.write(f"Meesage: \n")

        logger.debug(f"Command: {command}\n")
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )

        await asyncio.gather(
            read_stream(process.stdout, log, "stdout"),
            read_stream(process.stderr, log, "stderr"),
        )

        await process.wait()
