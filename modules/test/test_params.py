from modules.model import LanguageModel
from modules.prompt.styles import *
from dataclasses import dataclass


@dataclass
class TestParams:
    model: LanguageModel
    prompt: RoleplayPrompt
    auxiliary_model: LanguageModel | None
    auxiliary_prompt: InstructPrompt | None