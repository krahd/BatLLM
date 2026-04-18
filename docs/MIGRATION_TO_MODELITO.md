Migration to `modelito` (recommended)
=====================================

This short guide shows the minimal steps to adopt the published `modelito`
package (https://github.com/krahd/modelito) in place of local Ollama helper
code. Use this as a lightweight migration PR that documents recommended
changes; follow up PRs can perform automated code changes where desired.

1. Add the published package to your project dependencies (pin the tested
   version):

   - Example (pyproject):

     modelito = "==0.1.1"

2. Replace local references to in-repo helpers with `modelito` helpers. Key
   recommendations:

   - Use `modelito.ollama_service` helper functions for lifecycle checks
     and `ensure_ollama_running()`.
   - Use `modelito.connector.OllamaConnector` for conversation history
     management.
   - Use `modelito.timeout.estimate_remote_timeout()` where you compute
     request timeouts for remote models.

3. Run the existing test suite with `modelito` installed (use TestPyPI for
   RC verification):

```bash
python -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple modelito==0.1.1
pytest -q
```

4. After verification, remove/archival the local `ollama_service` helpers and
   replace imports. If you want I can prepare an automated PR that replaces
   a set of import sites and updates CI to install `modelito`.
