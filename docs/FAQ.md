> ![BatLLM logo](./images/logo-small.png) **[Project](../README.md) · [Documentation](README.md) · [User Guide](USER_GUIDE.md) · [FAQ](FAQ.md) · [Contributing](CONTRIBUTING.md) · [Status](../STATUS.md) · [Releases](https://github.com/krahd/BatLLM/releases)**

# FAQ

## What is BatLLM for?

BatLLM is a local, two-player battle game and a research/education project. It makes prompt-writing, model behaviour, context design, and failure modes concrete by requiring players to act through language models rather than through direct controls.

It is not a general-purpose chat application or inference server.

## Is there a single-player mode?

No. The current game assumes two human players and two model-mediated bots. There are no NPC opponents or campaign modes.

## Why can a good strategy still fail?

A strategy must survive several translations: the player expresses it in language, the model interprets it, and the response must match BatLLM's strict command language. Model choice, wording, conversation history, prompt augmentation, and shared or independent contexts can all change the result.

## What does Ollama do?

Ollama runs the local language model. BatLLM uses `modelito` to send gameplay requests and perform model-management operations, while the in-app Ollama controls also use the local `ollama` command-line installation for service lifecycle work.

## What happens when Ollama is missing or stopped?

BatLLM can offer to open the official installer when the CLI is missing. When Ollama is installed but stopped, BatLLM can ask to start it or start it automatically when **Start Ollama Automatically on BatLLM Launch** is enabled.

## What is the difference between local and remote models?

- A **local model** is already installed in Ollama and can be selected for play.
- A **remote model** is a catalogue entry. It must be downloaded before it becomes local and playable.

## Does BatLLM change the real Ollama installation?

Yes. Starting or stopping Ollama, downloading models, deleting models, and reinstalling Ollama affect the configured local environment. The Ollama screen is a real system control surface, not a BatLLM-only sandbox.

## What does **Use Selected** do?

It saves the chosen local model as `llm.model`, attempts to warm it for gameplay, and records it as `llm.last_served_model` after successful warm-up. Per-model timeout editing is separate and is stored in `llm.model_timeouts`.

## What are independent and shared contexts?

With independent contexts, each bot has its own model conversation history. With shared context, both bots use one history, which can expose earlier instructions or create interference between strategies.

Every new game starts with fresh conversation history.

## Can I review a saved game later?

Yes. **Save Session** writes a session-v2 JSON file that can be opened in the built-in or standalone Game Analyzer. The analyzer replays the saved commands using the frozen rules recorded with each round.

Legacy top-level list exports are intentionally unsupported.

## Where are configuration and sessions stored?

It depends on the launch method:

- a source checkout without `BATLLM_HOME` writes configuration to `src/configs/config.yaml` and relative sessions inside the repository;
- when `BATLLM_HOME` is set, mutable configuration and relative session folders resolve below that directory;
- Homebrew sets `BATLLM_HOME` to `~/Library/Application Support/BatLLM` by default;
- release bundles currently keep state relative to the extracted bundle unless the variable is set manually.

See [STATE_AND_INSTALLATION.md](STATE_AND_INSTALLATION.md).

## Can I manage Ollama outside BatLLM?

Yes. If Ollama is already installed, running, and reachable at the configured host and port, BatLLM can use it without the in-app service controls.

## What should I inspect when a bot does nothing?

Open **History**. The most common cause is that the model returned prose or another string that did not match one valid command. Also inspect the Ollama output log for service or timeout failures.

## What should contributors run before a pull request?

At minimum:

```bash
python run_tests.py non-live
python tools/check_docs.py
```

Use the area-specific guidance in [CONTRIBUTING.md](CONTRIBUTING.md), and run stateful live or install-level checks only when their side effects are acceptable.
