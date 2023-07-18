import os
import datetime
import re
from tqdm import tqdm  # type: ignore
from colorama import Fore

__all__ = ("Logger",)


class Logger:
    log_folder = str()
    log_file = str()
    print_verbose = False

    @classmethod
    def init(cls):
        cls.log_folder = "logs"
        if not os.path.exists(cls.log_folder):
            os.makedirs(cls.log_folder)
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")
        cls.log_file = os.path.abspath(os.path.join(cls.log_folder, f"log_{timestamp}.txt"))

    @classmethod
    def log(cls, message: str, verbose: bool = False):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        if cls.print_verbose or not verbose:
            if cls.print_verbose and verbose:
                message = f"{Fore.MAGENTA}{message.replace(Fore.RESET, Fore.RESET + Fore.MAGENTA)}{Fore.RESET}"
            tqdm.write(message)

        if cls.log_file:
            message = re.sub(r"\x1b\[\d+m", "", message)
            with open(cls.log_file, "a", encoding='utf-8') as file:
                file.write(f"[{timestamp}] {message}\n")

    @classmethod
    def log_event(cls, event: str, color: str, message: str, verbose: bool = False):
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")

        message = f"{color}{event}{Fore.RESET}: {message}"

        if cls.print_verbose or not verbose:
            if cls.print_verbose and verbose:
                message = f"{Fore.MAGENTA}{message.replace(Fore.RESET, Fore.RESET + Fore.MAGENTA)}{Fore.RESET}"
            tqdm.write(message)

        if cls.log_file:
            message = re.sub(r"\x1b\[\d+m", "", message)
            with open(cls.log_file, "a", encoding='utf-8') as file:
                file.write(f"[{timestamp}] {message}\n")
