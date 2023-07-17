import abc

__all__ = ("Prompt",)


class Prompt(abc.ABC):
    def __init__(self, format: dict):
        self.format = format

    @abc.abstractmethod
    def to_string(self):
        return ""