import subprocess
import json
import signal
from dataclasses import dataclass

current_process = None
current_secondary_process = None

@dataclass
class ModelParams:
    model_backend: str
    model_backend_host: str
    model_backend_path: str
    model_path: str
    model_format: str
    model_preset: str

def get_run_command(model: ModelParams, context_size: int, thread_number: int, port: int, extra_args: str) -> str:
    if model.model_backend == "koboldcpp":
        command = f"{model.model_backend_path} --model \"{model.model_path}\" --contextsize {context_size} --threads {thread_number} --stream --port {port} {extra_args}"
    elif model.model_backend == "llamacpp":
        command = f"{model.model_backend_path} -m \"{model.model_path}\" -t {thread_number} -c {context_size} --port {port} {extra_args}"
    else:
        return ""
    return command


def run_python_script(model: ModelParams, secondary_model: ModelParams | None, context_size: int, extra_args: str):
    command = f"python main.py --format {model.model_format} --context {context_size} --preset {model.model_preset} {extra_args}"

    if model.model_backend == "koboldcpp":
        command += f" --kcpp-host {model.model_backend_host}"
    elif model.model_backend == "llamacpp":
        command += f" --lcpp-host {model.model_backend_host}"
    elif model.model_backend == "llamapy":
        command += f" --lpy-model {model.model_path}"

    if secondary_model:
        command += f" --secondary-format {secondary_model.model_format} --secondary-preset {secondary_model.model_preset}"

        if secondary_model.model_backend == "koboldcpp":
            command += f" --kcpp-secondary-host {secondary_model.model_backend_host}"
        elif secondary_model.model_backend == "llamacpp":
            command += f" --lcpp-secondary-host {secondary_model.model_backend_host}"
        elif secondary_model.model_backend == "llamapy":
            command += f" --lpy-secondary-model {secondary_model.model_path}"

    subprocess.run(command, shell=True)

def exit_gracefully(signum, frame):
    global current_process
    if current_process is not None and current_process.poll() is None:
        current_process.terminate()
        current_process.wait()
        current_process = None
    global current_secondary_process
    if current_secondary_process is not None and current_secondary_process.poll() is None:
        current_secondary_process.terminate()
        current_secondary_process.wait()
        current_secondary_process = None
    exit()

def run_test_plan(test_plan_file):
    global current_process
    global current_secondary_process

    with open(test_plan_file, "r") as f:
        test_plan = json.load(f)

    signal.signal(signal.SIGINT, exit_gracefully)

    for item in test_plan:
        model_backend = item["model_backend"]
        if model_backend not in ["koboldcpp", "llamacpp", "llamapy"]:
            print(f"Invalid model_backend: {model_backend}")
            continue

        model = ModelParams(
            model_backend,
            item.get("model_backend_host", ""),
            item.get("model_backend_path", ""),
            item.get("model_path", ""),
            item["model_format"],
            item.get("model_preset", "default")
        )
        model_backend_args = item.get("model_backend_args", "")

        secondary_model_backend = item.get("secondary_model_backend", "")
        secondary_model_backend_args = item.get("secondary_model_backend_args", "")

        secondary_model = None
        if secondary_model_backend:
            if model_backend not in ["koboldcpp", "llamacpp", "llamapy"]:
                print(f"Invalid secondary_model_backend: {model_backend}")
                continue

            secondary_model = ModelParams(
                secondary_model_backend,
                item.get("secondary_model_backend_host", ""),
                item.get("secondary_model_backend_path", ""),
                item.get("secondary_model_path", ""),
                item["secondary_model_format"],
                item.get("secondary_model_preset", "default")
            )

        context_size = item.get("context_size", 2048)
        thread_number = item["thread_number"]
        extra_args = item.get("extra_args", "")

        if not model.model_backend_host:
            model.model_backend_host = "127.0.0.1:5000"
            run_command = get_run_command(model, context_size, thread_number, 5000, model_backend_args)
            if run_command:
                if current_process is not None and current_process.poll() is None:
                    # Terminate the current process if the parameters don't match
                    if current_process.args != run_command:
                        current_process.terminate()
                        current_process.wait()
                        current_process = subprocess.Popen(run_command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    current_process = subprocess.Popen(run_command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if secondary_model:
            if not secondary_model.model_backend_host:
                secondary_model.model_backend_host = "127.0.0.1:5001"
                run_command = get_run_command(secondary_model, 2048, thread_number, 5001, secondary_model_backend_args)
                if run_command:
                    if current_secondary_process is not None and current_secondary_process.poll() is None:
                        # Terminate the current process if the parameters don't match
                        if current_secondary_process.args != run_command:
                            current_secondary_process.terminate()
                            current_secondary_process.wait()
                            current_secondary_process = subprocess.Popen(run_command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        current_secondary_process = subprocess.Popen(run_command, shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_python_script(model, secondary_model, context_size, extra_args)

    # If the script is exiting, terminate the current process
    if current_process is not None and current_process.poll() is None:
        current_process.terminate()
        current_process.wait()
        current_process = None

    if current_secondary_process is not None and current_secondary_process.poll() is None:
        current_secondary_process.terminate()
        current_secondary_process.wait()
        current_secondary_process = None

if __name__ == "__main__":
    test_plan_file = "test_plan.json"
    run_test_plan(test_plan_file)