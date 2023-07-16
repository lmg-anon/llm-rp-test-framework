
from modules.model import LanguageModel
from modules.log import Logger
from colorama import Fore
import requests
import json
import time

__all__ = ("LcppModel",)


class LcppModel(LanguageModel):
    def __init__(self, lcpp_host: str, max_context: int, secondary: bool = False):
        assert(isinstance(lcpp_host, str))
        self.lcpp_host = lcpp_host
        super().__init__(max_context, secondary)

    def wait(self):
        wait_started = False
        while True:
            try:
                response = requests.get(f"http://{self.lcpp_host}/")
                break
            except Exception as e:
                if not wait_started:
                    Logger.log(f"{self.get_identifier()} is offline, waiting for it to become online...")
                    wait_started = True
                time.sleep(1)
                continue

    def _convert_data(self, data: dict, stream: bool = False) -> dict:
        if "max_context_length" in data:
            data["n_ctx"] = data["max_context_length"]
            del data["max_context_length"]
        if "max_tokens" in data:
            data["n_predict"] = data["max_tokens"]
            del data["max_tokens"]
        if "max_length" in data:
            data["n_predict"] = data["max_length"]
            del data["max_length"]
        if "rep_pen" in data:
            data["repeat_penalty"] = data["rep_pen"]
            del data["rep_pen"]
        if "rep_pen_range" in data:
            data["repeat_last_n"] = data["rep_pen_range"]
            del data["rep_pen_range"]
        if "tfs" in data:
            data["tfs_z"] = data["tfs"]
            del data["tfs"]
        if "typical" in data:
            data["typical_p"] = data["typical"]
            del data["typical"]
        if "sampler_seed" in data:
            data["seed"] = data["sampler_seed"]
            del data["sampler_seed"]
        if "stop_sequence" in data:
            data["stop"] = data["stop_sequence"]
            del data["stop_sequence"]
        else:
            data["stop"] = []
        data["n_keep"] = -1
        return data

    def _generate_once(self, data: dict) -> str:
        data = self._convert_data(data)
        response_text = str()

        for _ in range(5):
            if response_text:
                break

            try:
                response = requests.post(f"http://{self.lcpp_host}/completion", data=json.dumps(data), headers={'Content-Type': 'application/json'})
            except Exception as e:
                Logger.log_event("Error", Fore.RED, f"Model backend is offline.")
                exit(-1)

            if response.status_code == 503 or response.status_code == 400: # Server busy.
                Logger.log(f"{self.get_identifier()} is busy, trying again in ten seconds...", True)
                time.sleep(10)
                continue

            if response.status_code != 200:
                Logger.log_event("Error", Fore.RED, f"{self.get_identifier()} returned an error. HTTP status code: {response.status_code}")
                exit(-1)

            try:
                response_dict = response.json()
                response_text = response_dict["content"]
                if not response_text and response_dict["stopped_eos"]:
                    return ""
            except Exception as e:
                Logger.log_event("Warning", Fore.YELLOW, f"{self.get_identifier()} returned an invalid response. Error while parsing: {e}", True)
                continue

        return response_text