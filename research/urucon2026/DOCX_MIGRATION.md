# DOCX manuscript migration

The URUCON 2026 paper is maintained directly in Microsoft Word using the supplied IEEE A4 template.

- Authoritative manuscript: `paper/BatLLM_URUCON_2026_Paper.docx`
- Original template: `paper/conference-template-a4.docx`
- LaTeX sources, bibliography files, build logs, generated PDFs, conversion scripts, and duplicate `main.docx` files have been removed.
- CI validates the Word package, renders it temporarily for A4 geometry and page-count checks, and does not commit that temporary PDF.

This migration prevents ambiguity about which file is current and ensures that edits occur in the same format used for submission.
