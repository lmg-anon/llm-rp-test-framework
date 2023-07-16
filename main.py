from typing import Callable
from tqdm import tqdm
from colorama import Fore, init as colorama_init
from modules.model import LanguageModel
from modules.model.backends import KcppModel, LcppModel, LPY_PRESENT
if LPY_PRESENT:
    from modules.model.backends import LpyModel
from modules.prompt.styles import *
from modules.log import Logger
from modules.test import TestParams
from modules.test.csv_test import prepare_csv_test
import argparse
import json
import csv
import glob
import importlib
import os
import random
import time

def load_csvs(folder: str) -> list[dict]:
    script_paths = glob.glob(folder)
    scripts = []

    for script_path in script_paths:
        script_name = os.path.splitext(os.path.basename(script_path))[0]
        with open(script_path, "r") as file:
            reader = csv.DictReader(file)
            test = {}
            test["canonical_name"] = script_name
            test["name"] = ' '.join(word.capitalize() for word in script_name.split('_'))
            settings_path = os.path.join("tests", f"{script_name}_settings.json")
            if os.path.exists(settings_path):
                with open(settings_path, "r") as file:
                    test["settings"] = json.load(file)
            else:
                test["settings"] = {
                    "card": "characters/Rin Tohsaka.json",
                    "user": "Jin"
                }
            test["tests"] = [row for row in reader]
            scripts.append(test)

    return scripts

def load_scripts(folder: str) -> list:
    script_paths = glob.glob(folder)
    scripts = []

    for script_path in script_paths:
        module = importlib.import_module(script_path[:-3].replace(os.sep, "."))
        module.canonical_name = os.path.splitext(os.path.basename(script_path))[0]  # type: ignore
        module.name = ' '.join(word.capitalize() for word in module.canonical_name.split('_'))  # type: ignore
        scripts.append(module)

    return scripts

def run_tests(tests: list[tuple[str, Callable]], passes: int, specific_test: str | None) -> tuple[int, int, int]:
    failures = 0
    successes = 0
    skipped = 0
    for description, test in tqdm(tests, bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET), leave=False):
        if specific_test is not None and specific_test.lower() != description.lower():
            Logger.log(f"\t[{Fore.WHITE}SKIP{Fore.RESET}] {description}")
            skipped += 1
            continue
        Logger.log(f"Running test \"{description}\":", True)
        success_count = 0
        for progress in tqdm(range(passes), desc=f"Test \"{description}\"", bar_format="{l_bar}%s{bar}%s{r_bar}" % (Fore.GREEN, Fore.RESET), leave=False):
            if test():
                success_count += 1
                if success_count >= passes // 2 + 1:
                    Logger.log(f"\t[{Fore.GREEN}PASS{Fore.RESET}] {description} (success rate: {(success_count / (progress+1)) * 100}%)")
                    successes += 1
                    break
        else:
            Logger.log(f"\t[{Fore.RED}FAIL{Fore.RESET}] {description} (success rate: {(success_count / passes) * 100}%)")
            failures += 1
    return failures, successes, skipped

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Roleplay Test Framework")

    parser.add_argument("--preset", type=str, help="model preset (default: default)")
    parser.add_argument("--context-size", type=int, help="model context size (default: 2048)")
    parser.add_argument("--format", type=str, help="model prompt format (default: alpaca)")
    if LPY_PRESENT:
        parser.add_argument("--lpy-model", type=str, help="model path for llama.py")
    parser.add_argument("--lcpp-host", type=str, help="host for llama.cpp server")
    parser.add_argument("--kcpp-host", type=str, help="host for koboldcpp")

    parser.add_argument("--secondary-preset", type=str, help="secondary model preset (default: precise)")
    parser.add_argument("--secondary-format", type=str, help="secondary model prompt format (default: alpaca)")
    if LPY_PRESENT:
        parser.add_argument("--lpy-secondary-model", type=str, help="secondary model path for llama.py")
    parser.add_argument("--lcpp-secondary-host", type=str, help="secondary host for llama.cpp server")
    parser.add_argument("--kcpp-secondary-host", type=str, help="secondary host for koboldcpp")

    parser.add_argument("--passes", type=int, help="number of test passes (default: 5)")
    parser.add_argument("--seed", type=int, help="initial rng seed")

    parser.add_argument("--test-suite", type=str, help="run specific test suite")
    parser.add_argument("--test", type=str, help="run specific test")
    #parser.add_argument("--skip-test-suite", type=str, help="skip specific test suite(s)", nargs="+")
    #parser.add_argument("--skip-test", type=str, help="skip specific test(s)", nargs="+")

    parser.add_argument("--verbose", action="store_true", help="enable verbose output")
    args = parser.parse_args()

    os.chdir(os.path.dirname(os.path.realpath(__file__)))
    colorama_init()
    Logger.init()

    if args.seed:
        random.seed(args.seed)
        LanguageModel.base_seed = args.seed

    if args.verbose:
        Logger.print_verbose = True

    if LPY_PRESENT and args.lpy_model:
        model = LpyModel(args.lpy_model, args.context_size if args.context_size else 2048)  # type: ignore
    elif args.lcpp_host:
        model = LcppModel(args.lcpp_host, args.context_size if args.context_size else 2048)
    elif args.kcpp_host:
        model = KcppModel(args.kcpp_host, args.context_size if args.context_size else 2048)
    else:
        Logger.log_event("Error", Fore.RED, "Unknown model backend, specify either --lpy_model or --kcpp_host.")
        exit(-1)
    model.wait()
    model.load_preset(f"presets/{(args.preset if args.preset else 'default')}.json")

    with open(f"formats/{(args.format if args.format else 'alpaca')}.json", "r") as file:
        prompt_format = json.load(file)

    prompt = RoleplayPrompt(prompt_format)

    secondary_model = None
    if LPY_PRESENT and args.lpy_secondary_model:
        secondary_model = LpyModel(args.lpy_secondary_model, 2048, True)  # type: ignore
    elif args.lcpp_secondary_host:
        secondary_model = LcppModel(args.lcpp_secondary_host, 2048, True)
    elif args.kcpp_secondary_host:
        secondary_model = KcppModel(args.kcpp_secondary_host, 2048, True)
    else:
        Logger.log("Secondary model not specified, some tests will be skipped.")

    secondary_prompt = None
    if secondary_model:
        secondary_model.wait()
        secondary_model.load_preset(f"presets/{(args.secondary_preset if args.secondary_preset else 'precise')}.json")

        with open(f"formats/{(args.secondary_format if args.secondary_format else 'alpaca')}.json", "r") as file:
            secondary_prompt_format = json.load(file)

        secondary_prompt = InstructPrompt(secondary_prompt_format)

    scripts = []
    scripts.extend(load_csvs("tests/*.csv"))
    scripts.extend([script for script in load_scripts("tests/*.py") if hasattr(script, "prepare_test")])
    scripts.extend(load_csvs("tests/*/*.csv"))
    scripts.extend([script for script in load_scripts("tests/*/*.py") if hasattr(script, "prepare_test")])

    Logger.log(f"Found {Fore.GREEN}{len(scripts)}{Fore.RESET} test suites.")

    start_time = time.time()

    tests_failed = 0
    tests_passed = 0
    tests_skipped = 0
    for script in scripts:
        os.chdir("tests")
        try:
            if isinstance(script, dict):
                suite_canonical_name = script["canonical_name"]
                suite_name = script["name"]
                tests = prepare_csv_test(model, prompt, script)
            else:
                suite_canonical_name = script.canonical_name
                suite_name = script.name
                tests = getattr(script, "prepare_test")(TestParams(model, prompt, secondary_model, secondary_prompt))

            if len(tests) == 0 or args.test_suite and (suite_name.lower() != args.test_suite.lower() and suite_canonical_name.lower() != args.test_suite.lower()):
                Logger.log(f"Skipped test suite \"{suite_name}\".")
                tests_skipped += len(tests)
                continue

            Logger.log(f"Running test suite \"{suite_name}\":")

            try:
                failures, successes, skipped = run_tests(tests, args.passes if args.passes else 5, args.test)
            except KeyboardInterrupt:
                break
            tests_failed += failures
            tests_passed += successes
            tests_skipped += skipped
        finally:
            os.chdir("..")

    Logger.log(f"\nCompleted {tests_failed + tests_passed + tests_skipped} tests in {int(time.time() - start_time)} seconds.")

    report_str = ""

    if tests_failed > 0:
        report_str += f"{Fore.RED}{tests_failed} failed{Fore.RESET} / "
    else:
        report_str += "0 failed / "

    if tests_passed > 0:
        report_str += f"{Fore.GREEN}{tests_passed} passed{Fore.RESET} / "
    else:
        report_str += "0 passed / "

    report_str += f"{tests_skipped} skipped"

    Logger.log(report_str)

