import re
try:
    import png
    PNG_PRESENT = True
except ModuleNotFoundError as e:
    PNG_PRESENT = False
import base64
import json
from .chat_log import ChatMessage, ChatLog

__all__ = ("CharacterCard",)


class CharacterCard:
    def __init__(self):
        self.name = str()
        self.description = str()
        self.greeting: ChatMessage
        self.example_messages: list[ChatLog] = []

    def read_json(self, json: dict):
        self.name = json["name"].strip()
        self.description = json["description"].strip()
        self.greeting = ChatMessage(self.name, False, json["first_mes"].strip())
        self.example_messages = []
        examples = filter(None, re.split("<start>", json["mes_example"], flags=re.IGNORECASE))
        for example in examples:
            if not example.strip():
                continue
            log = ChatLog(self)
            log.read(example.strip())
            self.example_messages.append(log)

    def load(self, file_path: str):
        if file_path.endswith('.json'):
            self._load_json(file_path)
        elif file_path.endswith('.png'):
            self._load_img(file_path)
        else:
            raise ValueError('Unsupported file format.')

    def _load_json(self, file_path: str):
        with open(file_path, "r") as file:
            self.read_json(json.load(file))

    def _load_img(self, file_path: str):
        if not PNG_PRESENT:
            raise Exception("Please install the pypng library to load image files.")

        # Get the chunks
        chunks = list(png.Reader(file_path).chunks())
        tEXtChunks = [chunk for chunkType, chunk in chunks if chunkType == b'tEXt']

        # Find the tEXt chunk containing the data
        data_chunk = None
        for tEXtChunk in tEXtChunks:
            if tEXtChunk.startswith(b'chara\x00'):
                data_chunk = tEXtChunk
                break

        if data_chunk is not None:
            # Extract the data from the tEXt chunk
            base64EncodedData = data_chunk[6:].decode('utf-8')
            data = base64.b64decode(base64EncodedData).decode('utf-8')

            return self.read_json(json.loads(data))
        else:
            return None

    def save_json(self, file_path: str):
        json_data = {
            "name": self.name,
            "description": self.description,
            "first_mes": self.greeting.message,
            "mes_example": "<start>\n" + "<start>\n".join(log.to_string_log() for log in self.example_messages)
        }
        with open(file_path, "w") as file:
            json.dump(json_data, file)

    def to_string(self, prompt_format: dict) -> str:
        examples = ""
        if self.example_messages:
            examples += prompt_format["new_example_chat"]
            examples += prompt_format["new_example_chat"].join([msg.to_string(prompt_format["user_msg"], prompt_format["char_msg"]) for msg in self.example_messages])
        return prompt_format["card"].format(desc=self.description) + (prompt_format["example_chats"].format(examples=examples) if examples else "")