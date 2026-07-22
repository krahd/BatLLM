# Paper files

- `main.tex`: authoritative IEEE-style source, written in British English.
- `results.tex`: generated experimental-result macros consumed by `main.tex`.
- `main.pdf`: four-page A4 submission PDF.
- `main.docx`: editable single-column Word version using British-English proofing metadata.
- `BatLLM_URUCON_2026_Paper.pdf` and `.docx`: descriptively named copies of the same deliverables.
- `build_docx.py`: reproducible LaTeX-to-DOCX conversion and formatting script.
- `references.bib`: machine-readable bibliography used by the DOCX build.
- `main.log`: successful LaTeX build log from the validated research artefact.

The PDF is the submission-formatted version. The DOCX preserves equations, citations, tables, section structure, and references in an editable layout; it is not intended to reproduce IEEE's two-column pagination.

## DOCX build dependencies

The editable document requires `pandoc`, `python-docx`, and an IEEE CSL style. On Ubuntu 24.04, install `citation-style-language-styles`; the builder also recognises standard Pandoc and TeX Live CSL locations.
