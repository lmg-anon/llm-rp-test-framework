from modules.model import LanguageModel
from modules.prompt.styles import *
from dataclasses import dataclass


@dataclass
class TestParams:
    model: LanguageModel
    prompt: RoleplayPrompt
    secondary_model: LanguageModel | None
    secondary_prompt: InstructPrompt | None