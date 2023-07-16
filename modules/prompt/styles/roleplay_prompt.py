from modules.prompt import CharacterCard, ChatLog, Prompt

__all__ = ("RoleplayPrompt",)


class RoleplayPrompt(Prompt):
    def __init__(self, format: dict):
        self.user_name = str()
        self.card: CharacterCard
        self.chat_log: ChatLog
        super().__init__(format)

    def init(self, user_name: str, card: CharacterCard, add_greeting: bool = True):
        self.user_name = user_name
        self.card = card
        self.chat_log = ChatLog(card)
        if add_greeting:
            self.add_message(self.card.greeting.sender, self.card.greeting.message)

    def add_messages_from_file(self, file_path: str):
        log = ChatLog(self.card)
        log.load(file_path)
        self.add_messages(log)

    def add_messages(self, log: ChatLog):
        self.chat_log.add_messages(log)

    def add_message(self, sender: str, msg: str, is_user: bool | None = None):
        self.chat_log.add_message(sender, msg, is_user)

    def to_string(self) -> str:
        value = self.format["system"]
        value += self.card.to_string(self.format)
        value += self.format["new_chat"]
        value += self.chat_log.to_string(self.format["user_msg"], self.format["char_msg"])
        return value.replace("{{char}}", self.card.name).replace("<BOT>", self.card.name).replace("{{user}}", self.user_name).replace("<USER>", self.user_name)