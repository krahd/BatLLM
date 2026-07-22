# Final URUCON publication failure

The editable DOCX build failed before repository packaging.

## Standard output

```text
```

## Standard error

```text
Traceback (most recent call last):
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/paper/build_docx.py", line 367, in <module>
    raise SystemExit(main())
                     ^^^^^^
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/paper/build_docx.py", line 354, in main
    f"--csl={_locate_ieee_csl()}",
             ^^^^^^^^^^^^^^^^^^
  File "/home/runner/work/BatLLM/BatLLM/research/urucon2026/paper/build_docx.py", line 123, in _locate_ieee_csl
    raise FileNotFoundError(
FileNotFoundError: IEEE CSL file not found; install TeX Live citation-style-language styles.
```
