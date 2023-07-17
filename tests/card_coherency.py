from typing import Callable
from modules.model import *
from modules.prompt import *
from modules.prompt.styles import *
from modules.log import Logger
from modules.test import TestParams
from colorama import Fore


def ask_for_age(model: LanguageModel, prompt: RoleplayPrompt, long_context: bool) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Rin Tohsaka.json")

    prompt.init("Jin", card, not long_context)
    if long_context:
        prompt.add_messages_from_file("characters/Rin Tohsaka.jsonl")

    prompt.add_message("Jin", "\"Hey, what is your age?\"")
    prompt.add_message(card.name, "\"Huh, what kind of question is this? I'm")

    result = model.generate(prompt, max_iter=1)
    if any(word in result.lower() for word in ["18", "eighteen"]):
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def ask_for_eye_color(model: LanguageModel, prompt: RoleplayPrompt, long_context: bool) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Rin Tohsaka.json")

    prompt.init("Jin", card, not long_context)
    if long_context:
        prompt.add_messages_from_file("characters/Rin Tohsaka.jsonl")

    prompt.add_message("Jin", "*For a moment I get lost in Rin's beautiful eyes. They are a nice tone of")

    result = model.generate(prompt, max_iter=1)
    if any(word in result.lower() for word in ["blue", "aqua", "cyan"]):
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def ask_for_school_name(model: LanguageModel, prompt: RoleplayPrompt, long_context: bool) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Rin Tohsaka.json")

    prompt.init("Jin", card, not long_context)
    if long_context:
        prompt.add_messages_from_file("characters/Rin Tohsaka.jsonl")

    prompt.add_message("Jin", "\"Hey, what is the name of our school again?\"")
    prompt.add_message(card.name, "\"Huh, what kind of question is this? You know very well it's called")

    result = model.generate(prompt, max_iter=1)
    if "homur" in result.lower():
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def example_clues(model: LanguageModel, prompt: RoleplayPrompt) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Chiharu.json")

    prompt.init("Jin", card, True)

    prompt.add_message("Jin", "*sigh*")
    prompt.add_message(card.name, "")

    result = model.generate(prompt, max_iter=5)
    if any(word in result.lower() for word in ["ignore", "tackle"]):
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def prepare_test(params: TestParams) -> list[tuple[str, Callable]]:
    return [
        (
            "Basic understanding 1",
            lambda: ask_for_age(params.model, params.prompt, False)
        ),
        (
            "Basic understanding 2",
            lambda: ask_for_eye_color(params.model, params.prompt, False)
        ),
        (
            "Basic understanding 3",
            lambda: ask_for_school_name(params.model, params.prompt, False)
        ),
        (
            "Basic understanding 1 (long context)",
            lambda: ask_for_age(params.model, params.prompt, True)
        ),
        (
            "Basic understanding 2 (long context)",
            lambda: ask_for_eye_color(params.model, params.prompt, True)
        ),
        (
            "Basic understanding 3 (long context)",
            lambda: ask_for_school_name(params.model, params.prompt, True)
        ),
        # TODO: Instructed action (Card example: "{{char}} always whistles when he sees a girl")
        # TODO: Double meaning dialog (Dialog example: "Let's play together!", but the character card leads you to understand that this isn't as innocent as it seems from the dialog alone)
        # TODO: Expected outcome 1 (Action example: "*{{char}} falls on {{user}}*", but the character card specifies that when this happens it always ends up in sexual situations)
        # TODO: Expected outcome 2 (Action example: "*{{user}} smiles suggestively to char*", but the character card specifies that when this happens {{char}} always slaps {{user}})
        # TODO: Limited movement (Action example: "*{{char}} feels her nose itching*", but {{char}} is paraplegic)
        # TODO: Limited eyesight (Action example: "*{{char}} needs to go to a grocery store*", but {{char}} is blind)
    ]
