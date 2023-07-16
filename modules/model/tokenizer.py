from sentencepiece import SentencePieceProcessor

__all__ = ('LlamaTokenizer',)


class LlamaTokenizer:
    def __init__(self):
        self.tokenizer = SentencePieceProcessor()

    def encode(self, text: str) -> list[int]:
        return self.tokenizer.Encode(text)

    def decode(self, ids: list[int]) -> str:
        return self.tokenizer.Decode(ids)