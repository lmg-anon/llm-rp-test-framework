import subprocess
import json
import signal
import sys
import shutil
import os
from dataclasses import dataclass

current_process = None
current_auxiliary_process = None

@dataclass
class ModelParams:
    model_backend: str
    model_backend_host: str
    model_backend_path: str
    model_path: str
    model_format: str
    model_preset: str

def find_program_path(program_name):
    """
    Find the path of a program in the system's PATH environment variable.
    Returns None if the program is not found.
    """
    return shutil.which(program_name)

def get_run_command(model: ModelParams, context_size: int, thread_number: int, port: int, extra_args: str) -> str:
    if model.model_backend == "ooba":
        command = f"\"{sys.executable}\" {model.model_backend_path} --model \"{model.model_path}\" --n_ctx {context_size} --max_seq_len {context_size} --compress_pos_emb {context_size // 2048} --threads {thread_number} --api --api-blocking-port {port} {extra_args}"
    elif model.model_backend == "koboldcpp":
        command = f"{model.model_backend_path} --model \"{model.model_path}\" --contextsize {context_size} --threads {thread_number} --stream --port {port} {extra_args}"
    elif model.model_backend == "llamacpp":
        command = f"{model.model_backend_path} -m \"{model.model_path}\" -t {thread_number} -c {context_size} --port {port} {extra_args}"
    else:
        return ""
    return command

def run_python_script(model: ModelParams, auxiliary_model: ModelParams | None, context_size: int, extra_args: str):
    command = f"\"{sys.executable}\" main.py --backend {model.model_backend} --format {model.model_format} --context {context_size} --preset {model.model_preset} {extra_args}"

    if model.model_backend in ["koboldcpp", "llamacpp", "ooba"]:
        command += f" --host {model.model_backend_host}"
    elif model.model_backend == "llamapy":
        command += f" --model {model.model_path}"

    if auxiliary_model:
        command += f" --auxiliary-backend {auxiliary_model.model_backend} --auxiliary-format {auxiliary_model.model_format} --auxiliary-preset {auxiliary_model.model_preset}"

        if auxiliary_model.model_backend in ["koboldcpp", "llamacpp", "ooba"]:
            command += f" --auxiliary-host {auxiliary_model.model_backend_host}"
        elif auxiliary_model.model_backend == "llamapy":
            command += f" --auxiliary-model {auxiliary_model.model_path}"

    subprocess.run(command, shell=True)

def exit_gracefully(signum, frame):
    global current_process
    if current_process is not None and current_process.poll() is None:
        current_process.terminate()
        current_process.wait()
        current_process = None
    global current_auxiliary_process
    if current_auxiliary_process is not None and current_auxiliary_process.poll() is None:
        current_auxiliary_process.terminate()
        current_auxiliary_process.wait()
        current_auxiliary_process = None
    exit()

def run_test_plan(test_plan_file):
    global current_process
    global current_auxiliary_process

    with open(test_plan_file, "r") as f:
        test_plan = json.load(f)

    signal.signal(signal.SIGINT, exit_gracefully)

    for item in test_plan:
        model_backend = item["model_backend"]
        if model_backend not in ["koboldcpp", "llamacpp", "llamapy", "ooba"]:
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

        auxiliary_model_backend = item.get("auxiliary_model_backend", "")
        auxiliary_model_backend_args = item.get("auxiliary_model_backend_args", "")

        auxiliary_model = None
        if auxiliary_model_backend:
            if model_backend not in ["koboldcpp", "llamacpp", "llamapy", "ooba"]:
                print(f"Invalid auxiliary_model_backend: {model_backend}")
                continue

            auxiliary_model = ModelParams(
                auxiliary_model_backend,
                item.get("auxiliary_model_backend_host", ""),
                item.get("auxiliary_model_backend_path", ""),
                item.get("auxiliary_model_path", ""),
                item["auxiliary_model_format"],
                item.get("auxiliary_model_preset", "default")
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
                        current_process = subprocess.Popen(run_command, cwd=os.path.dirname(os.path.realpath(model.model_backend_path)), shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    current_process = subprocess.Popen(run_command, cwd=os.path.dirname(os.path.realpath(model.model_backend_path)), shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        if auxiliary_model:
            if not auxiliary_model.model_backend_host:
                auxiliary_model.model_backend_host = "127.0.0.1:5001"
                run_command = get_run_command(auxiliary_model, 2048, thread_number, 5001, auxiliary_model_backend_args)
                if run_command:
                    if current_auxiliary_process is not None and current_auxiliary_process.poll() is None:
                        # Terminate the current process if the parameters don't match
                        if current_auxiliary_process.args != run_command:
                            current_auxiliary_process.terminate()
                            current_auxiliary_process.wait()
                            current_auxiliary_process = subprocess.Popen(run_command, cwd=os.path.dirname(os.path.realpath(auxiliary_model.model_backend_path)), shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    else:
                        current_auxiliary_process = subprocess.Popen(run_command, cwd=os.path.dirname(os.path.realpath(auxiliary_model.model_backend_path)), shell=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        run_python_script(model, auxiliary_model, context_size, extra_args)

    # If the script is exiting, terminate the current process
    if current_process is not None and current_process.poll() is None:
        current_process.terminate()
        current_process.wait()
        current_process = None

    if current_auxiliary_process is not None and current_auxiliary_process.poll() is None:
        current_auxiliary_process.terminate()
        current_auxiliary_process.wait()
        current_auxiliary_process = None

if __name__ == "__main__":
    test_plan_file = "test_plan.json"
    run_test_plan(test_plan_file)