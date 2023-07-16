# RP Test Framework

This is a project that aims to make it easier to evaluate large language models capabilities at roleplaying with different presets/formats.

This project is still very experimental right now and doesn't feature many tests, any feedback and contributions are welcome.

## Usage

### Get the Code

```bash
git clone https://github.com/lmg-anon/llm-rp-test-framework
cd llm-rp-test-framework
```

### Prepare Environment

First you will need to install the python dependencies.

```bash
python3 -m pip install -r requirements.txt
```

Next you will need to create a file `test_plan.json`, you can just edit the `test_plan.json.default`, for more information see the table below.

| Argument | Description |
| --- | --- |
| model_backend | What will be used for inference (Currently supported: "llamacpp", "koboldcpp", "llamapy") |
| model_backend_host | The host to connect when using the llamacpp/koboldcpp backend, if not specified a new process will be started. |
| model_backend_path | The path to the backend server executable. Only applicable for llamacpp/koboldcpp backends, only necessary when "model_backend_host" is not specified. |
| model_path | The path to the large language model weights. Only necessary when "model_backend_host" is not specified. |
| model_format | The prompt format that will be used for the model. It must be one of the files inside the "formats" folder without it's extension. |
| model_preset | The configuration preset that will be used for the inference. It must be one of the files inside the "presets" folder without it's extension. (Default: default) |
| model_backend_args | Extra arguments that should be passed to the backend server. (Optional) |
| secondary_model_* | The above descriptions also apply to these arguments. The only differences is that it will be used for the secondary model, and all the secondary model options are optional. |
| context_size | The model context size. (Default: 2048) |
| thread_number | The number of threads to use for inference. |
| extra_args | Extra arguments that should be passed to the main script. (Optional) |

### Run

```bash
python3 test_runner.py
```

If the file `test_plan.json` is correct, the testing should start in your console. You can check verbose logs of the tests by opening the latest log in the `logs` folder or by using the `--verbose` flag in the `extra_args` argument of your `test_plan.json`.
Please be aware that there aren't many tests yet, and not all of them may support models with 2048 context.

#### Advanced Usage

The `test_runner.py` script is just a simple helper over the main script, you can use it directly if you (for some reason) need more control over the test.

```bash
usage: main.py [-h] [--preset PRESET] [--context-size CONTEXT_SIZE] [--format FORMAT] [--lpy-model LPY_MODEL]
               [--lcpp-host LCPP_HOST] [--kcpp-host KCPP_HOST] [--secondary-preset SECONDARY_PRESET]
               [--secondary-format SECONDARY_FORMAT] [--lpy-secondary-model LPY_SECONDARY_MODEL]
               [--lcpp-secondary-host LCPP_SECONDARY_HOST] [--kcpp-secondary-host KCPP_SECONDARY_HOST]
               [--passes PASSES] [--seed SEED] [--test-suite TEST_SUITE] [--test TEST] [--verbose]

Roleplay Test Framework

options:
  -h, --help            show this help message and exit
  --preset PRESET       model preset (default: default)
  --context-size CONTEXT_SIZE
                        model context size (default: 2048)
  --format FORMAT       model prompt format (default: alpaca)
  --lpy-model LPY_MODEL
                        model path for llama.py
  --lcpp-host LCPP_HOST
                        host for llama.cpp server
  --kcpp-host KCPP_HOST
                        host for koboldcpp
  --secondary-preset SECONDARY_PRESET
                        secondary model preset (default: precise)
  --secondary-format SECONDARY_FORMAT
                        secondary model prompt format (default: alpaca)
  --lpy-secondary-model LPY_SECONDARY_MODEL
                        secondary model path for llama.py
  --lcpp-secondary-host LCPP_SECONDARY_HOST
                        secondary host for llama.cpp server
  --kcpp-secondary-host KCPP_SECONDARY_HOST
                        secondary host for koboldcpp
  --passes PASSES       number of test passes (default: 5)
  --seed SEED           initial rng seed
  --test-suite TEST_SUITE
                        run specific test suite
  --test TEST           run specific test
  --verbose             enable verbose output
```

## More Information

### Secondary Model

The secondary model is a model used for questioning the correctness of the primary model output. It is used for tests that are more tricky than simply checking a list of expected words.

If we use the `alpaca` format, the secondary model would be prompted like this:
```
Below is an instruction that describes a task. Write a response that appropriately completes the request.

### Instruction:
Read the following message:
{model output}

Question: {question about the output}? Answer with Yes or No.

### Response:
```

### Test Suites

All files inside the `tests` folder are the test suites used for RP testing, each file contains multiple tests inside that test a particular aspect of the roleplay.
Currently only python scripts and csv files are supported as test suites.

#### Python Test Suites

It's recommended that this format is used for complex tests that require non-trivial reasoning, however, there are some basic tests available using the python format to make it easier to understand the code structure of the project. (also, it's still necessary to expand the capabilities of the other test formats)

The below function is an example of an python test:

```py
def ask_for_eye_color(model: LanguageModel, prompt: RoleplayPrompt) -> bool:
    model.new_seed()

    card = CharacterCard()
    card.load("characters/Rin Tohsaka.json")

    prompt.init("Jin", card, add_greeting=False)
    prompt.add_message("Jin", "*For a moment I get lost in Rin's beautiful eyes. They are a nice tone of")

    result = model.generate(prompt, max_iter=1)
    if any(word in result.lower() for word in ["blue", "aqua", "cyan"]):
        Logger.log_event("Success", Fore.GREEN, repr(result), True)
        return True
    Logger.log_event("Failure", Fore.RED, repr(result), True)
    return False
```

The tests are as self-contained as possible, this hopefully should make the creation of tests very painless.

#### CSV Test Suites

The CSV format should be used for trivial tests that, for example, only require an word to be present in the output.

The below CSV is an example of one of such tests:

```csv
description,message_input,message_output,expected_output
Simple math 1,"""How much is 888 + 88?""","""888 + 88 is equal to",976
Simple math 2,"""What is the result of 7 multiplied by 8?""","""7 multiplied by 8 is equal to",56
Simple math 3,"""What is the value of x if you solve the equation 2x + 5 = 17 for x?""","""x is equal to",6
```
