# Final URUCON publication failure

Exception: `CalledProcessError: Command '('/opt/hostedtoolcache/Python/3.12.13/x64/bin/python', '/home/runner/work/BatLLM/BatLLM/research/urucon2026/paper/build_docx.py')' returned non-zero exit status 1.`

```text
Traceback (most recent call last):
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/publish_repository_guard.py", line 24, in main
    return publish_repository.main()
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/publish_repository.py", line 232, in main
    build_documents()
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/publish_repository.py", line 62, in build_documents
    run(sys.executable, str(RESEARCH / "paper/build_docx.py"))
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/publish_repository.py", line 21, in run
    result = subprocess.run(
             ^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.12.13/x64/lib/python3.12/subprocess.py", line 571, in run
    raise CalledProcessError(retcode, process.args,
subprocess.CalledProcessError: Command '('/opt/hostedtoolcache/Python/3.12.13/x64/bin/python', '/home/runner/work/BatLLM/BatLLM/research/urucon2026/paper/build_docx.py')' returned non-zero exit status 1.
```
