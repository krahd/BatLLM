# Paper files

- `BatLLM_URUCON_2026_Paper.docx`: the sole authoritative manuscript and the file to edit or submit.
- `conference-template-a4.docx`: the original IEEE A4 Word template used to format the manuscript.

The paper is maintained directly in Microsoft Word. There is no LaTeX source, generated PDF, conversion script, duplicate `main.docx`, or separate bibliography file in this directory. This deliberately leaves one unambiguous current manuscript.

## Formatting and validation

The authoritative DOCX retains the template's A4 page geometry, two-column body layout, title and affiliation block, heading hierarchy, equations, table styles, reference numbering, and British-English proofing metadata. The repository workflow checks the DOCX package structurally, confirms that template guidance text has been removed, renders it temporarily with LibreOffice, and verifies an A4 page count within the conference limit. The temporary PDF is a validation artefact and is not committed as a second paper version.
