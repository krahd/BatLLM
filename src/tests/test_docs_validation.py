"""Keep documentation validation scoped to project content."""
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path


SPEC = spec_from_file_location("batllm_check_docs", Path(__file__).resolve().parents[2] / "tools/check_docs.py")
check_docs = module_from_spec(SPEC)
SPEC.loader.exec_module(check_docs)


def test_documentation_scan_excludes_dependencies_and_generated_files(monkeypatch, tmp_path):
    """Dependency documentation must not break the repository's link checks."""
    included = ["README.md", "docs/USER_GUIDE.md", ".github/CONTRIBUTING.md"]
    excluded = [
        ".venv_BatLLM/Lib/site-packages/win32comext/mapi/NOTICE.md",
        ".venv/lib/python3.12/site-packages/example/README.md",
        "venv/lib/README.md",
        "node_modules/example/README.md",
        "dist/releases/README.md",
        "build/README.md",
        "docs/code/README.md",
    ]
    for name in included + excluded:
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("[missing](missing-file.md)\n", encoding="utf-8")
    monkeypatch.setattr(check_docs, "ROOT", tmp_path)
    assert set(check_docs.markdown_files()) == {tmp_path / name for name in included}
