# Maintainer audit checklist

Use this checklist before release or after changing launch, configuration, packaging, or Ollama lifecycle code.

## Functional checks

- `python run_tests.py` passes on Python 3.10, 3.11, and 3.12.
- Application launch works from source checkout.
- Analyzer launch works from source checkout.
- Homebrew launcher and release-bundle launcher call the same canonical application entry path.
- Changing model selection updates only the user state directory.
- Saved sessions are written under the user state directory.
- Legacy session files either migrate deterministically or fail with a clear compatibility message.

## Security and dependency checks

- `pip-audit -r requirements.txt` passes or accepted findings are documented.
- Dependency Review passes on pull requests that change dependencies.
- Dependabot pull requests are reviewed and merged or explicitly rejected.
- No launcher uses untrusted shell interpolation.
- Subprocess calls use explicit argument lists, bounded timeouts, and clear error propagation.

## Platform checks

- Linux, macOS, and Windows CI pass.
- `BATLLM_HOME` works on all supported platforms.
- Paths with spaces and non-ASCII characters are tested.
- Missing Ollama, stopped Ollama, and non-responsive Ollama produce actionable errors.
