from __future__ import annotations
import argparse
import questionary
from loguru import logger
from config import ConfigManager, PROGRAM_NAME


class NotWanted(Exception):
    pass


async def get_user_choice(choices: list[str]) -> str:
    choice = await questionary.select(
        "Choose the command: (CTRL+C to exit)", choices=choices
    ).ask_async()
    if choice not in choices:
        raise ValueError("Invalid choice")
    return choice


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=f"{PROGRAM_NAME.upper()}: Run commands and fix errors using GPT."
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument("--model", default="gpt-3.5-turbo", help="GPT model")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    run_parser = subparsers.add_parser("run", help="Run a command")
    run_parser.add_argument(
        "command", nargs=argparse.REMAINDER, help="The command to run"
    )

    gpt_parser = subparsers.add_parser("ask", help="Get a command suggestion from GPT")
    gpt_parser.add_argument(
        "prompt",
        nargs=argparse.REMAINDER,
        help="The prompt to get a recommended command from GPT",
    )

    fix_parser = subparsers.add_parser("fix", help="Fix the last error")

    return parser


def get_openai_key() -> str:
    openai_key = ConfigManager().get("openai_key")
    if openai_key:
        return openai_key
    logger.info("No OPENAI key configured")
    openai_key = input("Please input your OPENAI key:").strip()
    ConfigManager().set("openai_key", openai_key)
    return openai_key


async def show_suggestion_and_select(suggestion: "Suggestion") -> str:
    from suggest import Suggestion

    logger.debug(suggestion.description)
    print(suggestion.description)

    if not suggestion.commands:
        logger.debug("No recommanded command needed.")
        print("No recommanded command needed.")
        exit()

    str_not_work = "None of above suggestion works"
    commands = [*suggestion.commands, str_not_work]
    command = await get_user_choice(commands)
    if command == str_not_work:
        raise NotWanted()
    return command


async def continue_or_exit():
    is_solved = await questionary.confirm("Is problem solved?").ask_async()
    if is_solved:
        exit()
