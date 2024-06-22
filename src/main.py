import asyncio

from loguru import logger
from config import ConfigManager
from interact import (
    NotWanted,
    create_parser,
    show_suggestion_and_select,
    continue_or_exit,
)
from history import read_last_log, execute_command
from suggest import (
    SuggestionType,
    UserInput,
    create_exclude_command_message,
    get_gpt_suggestions,
)


async def query_and_excute(user_input: UserInput, model: str) -> None:
    not_wanted_commands: list[str] = []
    while True:
        messages = user_input.create_message()
        if not_wanted_commands:
            messages.append(create_exclude_command_message(not_wanted_commands))
        suggestion = await get_gpt_suggestions(messages, model)
        try:
            command = await show_suggestion_and_select(suggestion)
            await execute_command(command)
            break
        except NotWanted as e:
            not_wanted_commands.extend(suggestion.commands)

    await continue_or_exit()
    logfile = ConfigManager().get_log_file()
    with open(logfile) as f:
        user_input.last_message += "\n---\n" + f.read()
    await query_and_excute(user_input, model)


async def main_async() -> None:
    ConfigManager()
    parser = create_parser()
    args = parser.parse_args()

    if args.subcommand == "run":
        await execute_command(" ".join(args.command))
    elif args.subcommand == "ask":
        user_input = UserInput(
            SuggestionType.ASK,
            text=" ".join(args.prompt),
        )
        await query_and_excute(user_input, args.model)
    elif args.subcommand == "fix":
        user_input = UserInput(
            SuggestionType.FIX,
            last_message=await read_last_log(),
        )
        await query_and_excute(user_input, args.model)


def main() -> None:
    asyncio.run(main_async())


if __name__ == "__main__":
    main()
