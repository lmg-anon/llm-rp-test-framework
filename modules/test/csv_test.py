from typing import Callable
from modules.model import *
from modules.prompt import *
from modules.prompt.styles import *
from modules.log import Logger
from colorama import Fore


def csv_test(model: LanguageModel, prompt: RoleplayPrompt, card: CharacterCard, log: ChatLog | None, settings: dict, test_info: dict) -> bool:
    greeting = True
    if "greeting" in settings:
        greeting = settings["greeting"]

    model.new_seed()
    prompt.init(settings["user"], card, greeting)
    if log:
        prompt.add_messages(log)

    max_iter = 1
    if "max_iter" in settings:
        max_iter = settings["max_iter"]

    prompt.add_message(settings["user"], test_info["message_input"])
    prompt.add_message(card.name, test_info["message_output"])

    for part, output in model.generate_iter(prompt, max_iter=max_iter):
        if test_info["expected_output"] in output:
            Logger.log_event("Success", Fore.GREEN, f"\"{test_info['expected_output']}\" found in {repr(part)}", True)
            return True
        Logger.log_event("Failure", Fore.RED, f"\"{test_info['expected_output']}\" not found in {repr(part)}", True)
    return False

def prepare_csv_test(model: LanguageModel, prompt: RoleplayPrompt, csv_info: dict) -> list[tuple[str, Callable]]:
    settings = csv_info["settings"]
    tests = csv_info["tests"]

    try:
        card = CharacterCard()
        card.load(settings["card"])

        log = None
        if "log" in settings:
            log = ChatLog(card)
            log.load(settings["log"])
    except:
        Logger.log_event("Error", Fore.RED, "Failed to load test suite.")
        return []

    # https://stackoverflow.com/a/2295368
    def create_test(test_info):
        return lambda: csv_test(model, prompt, card, log, settings, test_info)

    return [(test_info["description"], create_test(test_info)) for test_info in tests]