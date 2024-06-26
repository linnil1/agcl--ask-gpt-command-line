import os
import sys
import pwd
import asyncio
import platform
from enum import StrEnum, auto
from typing import TextIO

import distro
from loguru import logger
from config import ConfigManager, PROGRAM_NAME


class Shell(StrEnum):
    BASH = auto()
    SH = auto()
    ASH = auto()
    ZSH = auto()
    UNKNOWN = auto()


def get_platform() -> str:
    return platform.platform() + " " + distro.name(pretty=True)


def get_username() -> str:
    try:
        return os.getlogin()
    except:
        pass
    return pwd.getpwuid(os.getuid()).pw_name


def get_history_file(shell: Shell) -> str:
    if shell == Shell.BASH:
        return os.path.expanduser("~/.bash_history")
    elif shell == Shell.ASH:
        return os.path.expanduser("~/.ash_history")
    elif shell == Shell.SH:
        return os.path.expanduser("~/.sh_history")
    elif shell == Shell.ZSH:
        return os.path.expanduser("~/.zsh_history")
    return ""


async def get_shell_name() -> Shell:
    result = await asyncio.create_subprocess_shell(
        f"ps -p {os.getppid()} -o comm=",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    stdout, stderr = await result.communicate()
    if result.returncode != 0:
        return Shell.ASH
    shell_name = stdout.decode().strip().split("/")[-1].lower()
    for shell in Shell:
        if shell.value == shell_name and os.path.exists(get_history_file(shell)):
            return shell
    return Shell.UNKNOWN


async def get_last_command(shell: Shell) -> str:
    with open(get_history_file(shell), "rb") as file:
        history_list = file.readlines()
        history_raw = history_list[-2]  # -1 is the current command
        history = history_raw.strip().decode()
        if shell == Shell.ZSH and ";" in history:
            history = history.split(";", 1)[1]
        return history


def read_saved_log() -> str:
    logfile = ConfigManager().get_log_file()
    with open(logfile) as f:
        return f.read()


async def read_last_log() -> str:
    shell = await get_shell_name()
    if shell == Shell.UNKNOWN:
        err_text = "Unknown shell OR Cannot read history!"
        logger.error(err_text)
        raise ValueError(err_text)
    last_command = await get_last_command(shell)
    if not last_command.startswith(PROGRAM_NAME):
        logger.info(
            f"Last command is not from {PROGRAM_NAME}, run again to capture stdout/stderr"
            f"command = {last_command}"
        )
        await execute_command(last_command)

    return read_saved_log()


async def read_stream(
    stream: asyncio.StreamReader, log: TextIO, stream_name: str
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
        log.write(f"Platform: {get_platform()}\n")
        log.write(f"Current Directory: {os.getcwd()}\n")
        log.write(f"Current User: {get_username()}\n")
        log.write(f"Command: {command}\n")
        log.write(f"Message:\n")

        logger.debug(f"Command: {command}\n")
        process = await asyncio.create_subprocess_shell(
            command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        assert process.stdout
        assert process.stderr

        await asyncio.gather(
            read_stream(process.stdout, log, "stdout"),
            read_stream(process.stderr, log, "stderr"),
        )

        await process.wait()
