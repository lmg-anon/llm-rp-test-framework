from modules.model import LanguageModel
from modules.log import Logger
from colorama import Fore
import requests
import json
import time

__all__ = ("OobaModel",)


class OobaModel(LanguageModel):
    def __init__(self, ooba_host: str, max_context: int, secondary: bool = False):
        assert(isinstance(ooba_host, str))
        self.ooba_host = ooba_host.strip('/')
        if not self.ooba_host.startswith("http"):
            self.ooba_host = f"http://{self.ooba_host}"
        super().__init__(max_context, secondary)

    def wait(self):
        wait_started = False
        while True:
            try:
                requests.get(f"{self.ooba_host}/")
                break
            except Exception as e:
                if not wait_started:
                    Logger.log(f"{self.get_identifier()} is offline, waiting for it to become online...")
                    Logger.log(e, True)
                    wait_started = True
                time.sleep(1)
                continue

    def _convert_data(self, data: dict, stream: bool = False) -> dict:
        def rename_dict_key(lhs: str, rhs: str):
            if lhs in data:
                data[rhs] = data[lhs]
                del data[lhs]
        rename_dict_key("max_context_length", "truncation_length")
        rename_dict_key("max_tokens", "max_new_tokens")
        rename_dict_key("max_length", "max_new_tokens")
        rename_dict_key("rep_pen", "repetition_penalty")
        rename_dict_key("rep_pen_range", "repetition_penalty_range")
        rename_dict_key("typical", "typical_p")
        rename_dict_key("sampler_seed", "seed")
        rename_dict_key("stop_sequence", "stopping_strings")
        return data

    def _generate_once(self, data: dict) -> str:
        data = self._convert_data(data)
        response_text = str()

        for _ in range(5):
            try:
                response = requests.post(f"{self.ooba_host}/api/v1/generate", data=json.dumps(data), headers={'Content-Type': 'application/json'})
            except Exception as e:
                Logger.log_event("Error", Fore.RED, f"{self.get_identifier()} is offline.")
                Logger.log(e, True)
                exit(-1)

            if response.status_code == 503: # Server busy.
                Logger.log(f"{self.get_identifier()} is busy, trying again in ten seconds...", True)
                time.sleep(10)
                continue

            if response.status_code != 200:
                Logger.log_event("Error", Fore.RED, f"{self.get_identifier()} returned an error. HTTP status code: {response.status_code}")
                exit(-1)

            try:
                response_text = response.json()["results"][0]["text"]
                if response_text:
                    break
            except Exception as e:
                Logger.log_event("Warning", Fore.YELLOW, f"{self.get_identifier()} returned an invalid response. Error while parsing: {e}", True)
                continue

        return response_text