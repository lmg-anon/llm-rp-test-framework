from modules.model import LanguageModel
from modules.log import Logger
from colorama import Fore
import requests
import json
import time

__all__ = ("KcppModel",)


class KcppModel(LanguageModel):
    def __init__(self, kcpp_host: str, max_context: int, auxiliary: bool = False):
        assert(isinstance(kcpp_host, str))
        self.kcpp_host = kcpp_host.strip('/')
        if not self.kcpp_host.startswith("http"):
            self.kcpp_host = f"http://{self.kcpp_host}"
        super().__init__(max_context, auxiliary)

    def wait(self):
        wait_started = False
        while True:
            try:
                requests.get(f"{self.kcpp_host}/")
                break
            except Exception as e:
                if not wait_started:
                    Logger.log(f"{self.get_identifier()} is offline, waiting for it to become online...")
                    Logger.log(str(e), True)
                    wait_started = True
                time.sleep(1)
                continue

    def _generate_once(self, data: dict) -> str:
        response_text = str()

        for _ in range(5):
            try:
                response = requests.post(f"{self.kcpp_host}/api/v1/generate", data=json.dumps(data), headers={'Content-Type': 'application/json'})
            except Exception as e:
                Logger.log_event("Error", Fore.RED, f"{self.get_identifier()} is offline.")
                Logger.log(str(e), True)
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