# Security Policy

## Supported versions

Security fixes are provided for the current `main` branch and the most recent tagged release.

## Reporting a vulnerability

Report suspected vulnerabilities privately. Do not open a public issue containing exploit details, secrets, local paths, or reproduction data that may expose a user system.

Include:

- affected BatLLM version or commit;
- operating system and Python version;
- installation method;
- whether Ollama was installed system-wide, through Homebrew, or manually;
- minimal reproduction steps;
- relevant logs with secrets, local usernames, and paths redacted.

## Security-relevant areas

BatLLM interacts with a local Ollama service, reads and writes local configuration, stores sessions, and invokes launch scripts. Reports involving path traversal, unsafe subprocess use, unexpected writes outside the configured application directory, dependency compromise, or unintended disclosure of local files should be treated as security relevant.
