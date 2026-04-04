> ![BatLLM logo](./images/logo-small.png) **[Overview](DOCUMENTATION.md) · [Readme](README.md) · [User Guide](USER_GUIDE.md) · [Configuration](CONFIGURATION.md) · [Testing](TESTING.md) · [Troubleshooting](TROUBLESHOOTING.md) · [Contributing](CONTRIBUTING.md) · [FAQ](FAQ.md) · [Changelog](CHANGELOG.md) · [Credits](CREDITS.md) · [Code Docs](code/html/index.html)**

# Changelog

## 2026-04-03

### Documentation

- replaced the placeholder main documentation page with a current project overview
- rewrote the README, user guide, contributor guide, and FAQ to match the current codebase
- added dedicated configuration, testing, and troubleshooting guides
- added an actual documentation landing page in `docs/index.html`
- added Ollama workflow diagrams for the control screen and model pickers
- aligned the docs with the current UI labels, including the `Ollama Config` button

### Ollama UX

- documented the modal model pickers, including `Esc` dismissal and outside-click dismissal
- documented the difference between local model selection and remote model download
- documented that BatLLM may stop the previously managed model before warming a newly selected one

### Repository Consistency

- added the missing `requests` and Python `ollama` dependencies to `requirements.txt`
- removed the stray space-prefixed `primary_color` key from config defaults and sample configs
