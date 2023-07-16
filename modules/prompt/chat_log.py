from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import CharacterCard
import json
from dataclasses import dataclass

__all__ = ("ChatMessage", "ChatLog",)


@dataclass
class ChatMessage:
    sender: str
    is_user: bool
    message: str

    def __repr__(self) -> str:
        return f"{self.sender}: {self.message}"

    def to_string(self, msg_format: str) -> str:
        return msg_format.format(name=self.sender, maybe_space=" " if self.message else "", msg=self.message)

class ChatLog:
    def __init__(self, character: 'CharacterCard'):
        self.character = character
        self.entries: list[ChatMessage] = []

    def __repr__(self) -> str:
        return repr("\n".join([str(entry) for entry in self.entries]))

    def read(self, text: str):
        self.entries = []

        sender = None
        message = ""
        for line in text.splitlines():
            if ":" in line:
                if sender is not None:
                    is_user = sender != self.character.name and sender != "{{char}}"
                    self.entries.append(ChatMessage(sender, is_user, message.strip()))

                sender, message = [s.strip() for s in line.split(':', 1)]
            else:
                message += " " + line.strip()

        if sender is not None:
            is_user = sender != self.character.name and sender != "{{char}}"
            self.entries.append(ChatMessage(sender, is_user, message.strip()))

    def load(self, file_path: str):
        with open(file_path, 'r') as file:
            if file_path.endswith('.jsonl'):
                self._load_jsonl(file)
            elif file_path.endswith('.txt'):
                self.read(file.read())
            else:
                raise ValueError('Unsupported file format.')

    def _load_jsonl(self, file):
        for line in file:
            entry = json.loads(line)
            if 'name' not in entry:
                continue
            self.entries.append(ChatMessage(entry['name'], entry['is_user'], entry['mes']))

    def add_message(self, sender: str, message: str, is_user: bool | None = None):
        self.entries.append(ChatMessage(sender, is_user if is_user else sender != self.character.name and sender != "{{char}}", message))

    def add_messages(self, log: 'ChatLog'):
        self.entries.extend(log.entries)

    def to_string(self, user_msg_format: str, char_msg_format: str) -> str:
        result = str()
        for entry in self.entries:
            result += entry.to_string(user_msg_format if entry.is_user else char_msg_format)
        return result

    def to_string_log(self) -> str:
        return "\n".join([f"{entry.sender}: {entry.message}" for entry in self.entries])