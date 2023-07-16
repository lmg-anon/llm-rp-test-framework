from modules.prompt import Prompt
from dataclasses import dataclass

__all__ = ("InstructPrompt",)


@dataclass
class ExchangeItem:
    is_response: bool
    text: str

class InstructPrompt(Prompt):
    def __init__(self, format: dict):
        self.exchange: list[ExchangeItem] = []
        super().__init__(format)

    def init(self):
        self.exchange = []

    def add_instruction(self, text):
        self.exchange.append(ExchangeItem(False, text))

    def add_question(self, text, question):
        self.exchange.append(ExchangeItem(False, f"Read the following message:\n{text.strip()}\n\nQuestion: {question}"))

    def add_response(self, text):
        self.exchange.append(ExchangeItem(True, text))

    def to_string(self) -> str:
        value = self.format["system"]
        if len(self.exchange) > 0 and not self.exchange[-1].is_response:
            self.exchange.append(ExchangeItem(True, ""))
        for item in self.exchange:
            value += self.format["response" if item.is_response else "instruction"].format(maybe_space=" " if item.text else "", text=item.text)
        return value