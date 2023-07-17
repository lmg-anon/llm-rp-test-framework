
from modules.model import LanguageModel
from llama_cpp import Llama

__all__ = ("LpyModel",)


class LpyModel(LanguageModel):
    def __init__(self, model_path: str, max_context: int, secondary: bool = False):
        self.new_seed()
        self.llm = Llama(model_path=model_path, n_ctx=max_context, seed=self.seed, verbose=False)  # type: ignore
        super().__init__(max_context, secondary)

    def __del__(self):
        del self.llm

    def wait(self):
        pass

    def _generate_once(self, data: dict) -> str:
        output = self.llm(
            data["prompt"],
            max_tokens=data["max_length"],
            temperature=data["temperature"],
            top_p=data["top_p"],
            echo=False,
            stop=data["stop_sequence"],
            #frequency_penalty=data["frequency_penalty"],
            #presence_penalty=data["presence_penalty"],
            repeat_penalty=data["rep_pen"],
            top_k=data["top_k"],
            #stream=True,
            tfs_z=data["tfs"]
        )
        return output["choices"][0]["text"]  # type: ignore