
from typing import Iterator
from modules.log import Logger
from modules.prompt import Prompt
from modules.prompt.styles import *
import json
import random
import abc

__all__ = ("LanguageModel",)


class LanguageModel(abc.ABC):
    base_seed = None

    def __init__(self, max_context: int, auxiliary: bool):
        self.max_context = max_context
        self.presets = dict()
        self.seed = LanguageModel.base_seed
        self.is_auxiliary = auxiliary

    def load_preset(self, file_path: str):
        with open(file_path, "r") as file:
            self.presets = json.load(file)

    def new_seed(self):
        self.seed = random.randint(1, 0xFFFFFFFF)
        Logger.log(f"New {'auxiliary ' if self.is_auxiliary else ''}model seed: {self.seed}", True)

    def clear_seed(self):
        self.seed = LanguageModel.base_seed

    def get_identifier(self) -> str:
        return f"Model backend{' (auxiliary)' if self.is_auxiliary else ''}"

    @abc.abstractmethod
    def wait(self):
        pass

    @abc.abstractmethod
    def _generate_once(self, data: dict) -> str:
        return ""

    def generate_iter(self, prompt: Prompt | str, max_tokens_per_iter: int = 8, max_iter: int = 0xFFFFFFFF) -> Iterator[tuple[str, str]]:
        if isinstance(prompt, RoleplayPrompt):
            stop_sequences = [s.replace("{{char}}", prompt.card.name).replace("<BOT>", prompt.card.name).replace("{{user}}", prompt.user_name).replace("<USER>", prompt.user_name) for s in prompt.format["stop_sequences"]]
        elif isinstance(prompt, InstructPrompt):
            stop_sequences = [s for s in prompt.format["stop_sequences"] if "{{char}}" not in s and "{{user}}" not in s]
        else:
            stop_sequences = ["\n##"]
        data = self.presets.copy()
        data.update({
            "max_context_length": self.max_context,
            "max_length": max_tokens_per_iter,
            "stop_sequence": stop_sequences
        })

        if self.seed:
            data["sampler_seed"] = self.seed

        prompt_str = prompt.to_string() if not isinstance(prompt, str) else prompt
        output_str = str()
        for _ in range(max_iter):
            data["prompt"] = prompt_str + output_str
            response_text = self._generate_once(data)

            # Return if we couldn't generate anything.
            if not response_text:
                return

            output_str += response_text
            if any((match := s) in output_str for s in stop_sequences):
                yield response_text.split(match, 2)[0], output_str.split(match, 2)[0]
                break
            yield response_text, output_str

    def generate(self, prompt: Prompt | str, max_tokens_per_iter: int = 8, max_iter: int = 0xFFFFFFFF) -> str:
        result = str()
        for _, output in self.generate_iter(prompt, max_tokens_per_iter, max_iter):
            result = output
        return result