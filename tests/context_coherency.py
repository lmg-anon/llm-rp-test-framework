from typing import Callable
from modules.model import *
from modules.prompt import *
from modules.prompt.styles import *
from modules.log import Logger
from modules.test import TestParams
from colorama import Fore
import re


def ask_for_location(model: LanguageModel, prompt: RoleplayPrompt) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Rin Tohsaka.json")

    prompt.init("Jin", card, False)
    prompt.add_messages_from_file("characters/Rin Tohsaka.jsonl")

    prompt.add_message("Jin", "\"Hey, where are we again? *I say as I look around*\"")
    prompt.add_message(card.name, "\"Hm...? We are at")

    result = model.generate(prompt, max_iter=1)
    if "my" in result.lower() and not "your" in result.lower():
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def event_memory(model: LanguageModel, prompt: RoleplayPrompt) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Rin Tohsaka.json")

    prompt.init("Jin", card, False)

    prompt.add_message("Jin", "*Suddenly a bucket of water falls on me and my clothes get drenched, so I take off my shirt.*")
    prompt.add_message(card.name, "\"W-What was this!? Are you okay Jin?\" *Rin says worried*")
    prompt.add_message("Jin", "\"I'm fine, don't worry...\" *I say a bit down, knowing I don't have a spare shirt*")
    prompt.add_messages_from_file("characters/Rin Tohsaka.jsonl")
    prompt.add_message("Jin", "\"Hey Rin, do you remember why I am not wearing a shirt?\" *I say while blushing slightly*")
    prompt.add_message(card.name, "")

    result = str()
    for _, output in model.generate_iter(prompt, max_iter=8):
        if any(word in output.lower() for word in ["rooftop", "bucket", "water", "drench", "damp", "wet", "soak"]):
            Logger.log_event("Success", Fore.GREEN, repr(output), True)
            return True
        result = output
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

# This is used to speed up the "understand_options" test.
g_ayre_replies = []

def follow_format(model: LanguageModel, prompt: RoleplayPrompt) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Training Young Lady.json")
    prompt.init("Jin", card, True)

    prompt.add_message("Jin", "3")
    prompt.add_message(card.name, "")

    first_part = model.generate(prompt, max_iter=1)
    if not first_part.strip().startswith("**["):
        Logger.log_event("Failure", Fore.RED, repr(first_part), True)
        return False

    # result = str()
    # for _, output in model.generate_iter(prompt):
    #     result = output
    result = model.generate(prompt)
    g_ayre_replies.append(result)

    pattern_start = r"^\*\*\[.*?\] \/ \[Ayre's room\] \/ \[Casual dress with stockings and low pumps\] \/ \[Affection: \d+\/\d+\] \/ \[Breasts: .*?\]\*\*"
    match_start = re.match(pattern_start, result.strip())

    pattern_end = r"\d\. .*?[\r\n]{1,2}\d\. .*?$"
    match_end = re.search(pattern_end, result.strip())

    if match_start is not None and match_end is not None:
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def understand_options(model: LanguageModel, prompt: RoleplayPrompt, secondary_model: LanguageModel | None, secondary_prompt: InstructPrompt | None) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Training Young Lady.json")
    prompt.init("Jin", card, True)

    prompt.add_message("Jin", "3") # 3. With a seductive smile, slowly approach her.
    prompt.add_message(card.name, "")

    result = g_ayre_replies.pop() if g_ayre_replies else ""
    if not result:
        first_part = model.generate(prompt, max_iter=1)
        if not first_part.strip().startswith("**["):
            Logger.log_event("Failure", Fore.RED, f"Incorrect format: {repr(first_part)}", True)
            return False
        for _, output in model.generate_iter(prompt):
            # Very simple check to speed up things.
            if "smirk" in output or "smile" in output and "seduct" in output:
                Logger.log_event("Success", Fore.GREEN, repr(output), True)
                return True
            result = output
    else:
        # Very simple check to speed up things.
        if "smirk" in result or "smile" in result and "seduct" in result:
            Logger.log_event("Success", Fore.GREEN, repr(result), True)
            return True

    if secondary_model is not None and secondary_prompt is not None:
        # We couldn't deduce if the answer was seductive from the simple check...
        # Let's use a secondary model to verify the answer.
        Logger.log(f"Questioning secondary model about correctness of output: {repr(result)}", True)

        yes = 0
        for i in range(5):
            secondary_model.new_seed()
            secondary_prompt.init()
            secondary_prompt.add_question(result, f"Is Jin smiling seductively and approaching Ayre? Answer with Yes or No.")

            answer = secondary_model.generate(secondary_prompt, max_iter=1)
            Logger.log(f"Secondary model response {i+1}: {answer.strip()}", True)

            if "yes" in answer.lower():
                yes += 1
                if yes >= 3:
                    Logger.log_event("Success", Fore.GREEN, "\"Yes\" threshold met.", True)
                    return True
            elif yes + 5 - (i + 1) < 3:
                Logger.log_event("Failure", Fore.RED, "\"Yes\" threshold wasn't met.", True)
                return False

    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False

def prepare_test(params: TestParams) -> list[tuple[str, Callable]]:
    return [
        (
            "Location awareness",
            lambda: ask_for_location(params.model, params.prompt)
        ),
        (
            "Memory of events (long context)",
            lambda: event_memory(params.model, params.prompt)
        ),
        (
            "Follow reply format",
            lambda: follow_format(params.model, params.prompt)
        ),
        (
            "Understand reply options",
            lambda: understand_options(params.model, params.prompt, params.secondary_model, params.secondary_prompt)
        )
        # TODO: Clothing awareness (At the start of the conversation: "*user removes shirt*", some messages later "*user drops water on himself*", and then "*char notices user dropped water all over his ...")
    ]
