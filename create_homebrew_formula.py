"""Generate a tap-ready Homebrew formula for BatLLM."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen


ROOT = Path(__file__).resolve().parent
VERSION_FILE = ROOT / "VERSION"
HOMEBREW_REQUIREMENTS = ROOT / "packaging" / "homebrew" / "requirements.txt"
DEFAULT_FORMULA_OUTPUT = ROOT / "packaging" / "homebrew" / "Formula" / "batllm.rb"
DEFAULT_PYTHON = Path("/opt/homebrew/bin/python3.12")
PYPI_USER_AGENT = "BatLLM Homebrew Formula Generator"
GITHUB_OWNER = "krahd"
GITHUB_REPO = "BatLLM"
EXTRA_BUILD_REQUIREMENTS = ["maturin==1.9.4"]
SOURCE_ONLY_PACKAGES = ("kivymd", "pydantic_core")


def read_version() -> str:
    """Read the BatLLM version string from VERSION."""
    return VERSION_FILE.read_text(encoding="utf-8").strip()


def read_requirements(path: Path) -> list[str]:
    """Read a simple requirements file, ignoring comments and empty lines."""
    requirements: list[str] = []
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


def sha256_file(path: Path) -> str:
    """Return the SHA-256 digest for a local file."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_url(url: str) -> str:
    """Download a URL and return its SHA-256 digest."""
    digest = hashlib.sha256()
    request = Request(url, headers={"User-Agent": PYPI_USER_AGENT})
    with urlopen(request) as response:
        for chunk in iter(lambda: response.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_downloaded_artifact_name(filename: str) -> tuple[str, str]:
    """Extract a PyPI project name and version from a downloaded artifact name."""
    name = Path(filename).name
    if name.endswith(".whl"):
        parts = name[:-4].split("-")
        if len(parts) < 5:
            raise ValueError(f"Unsupported wheel filename: {filename}")
        return parts[0], parts[1]

    for suffix in (".tar.gz", ".zip"):
        if name.endswith(suffix):
            stem = name[: -len(suffix)]
            project_name, version = stem.rsplit("-", 1)
            return project_name, version

    raise ValueError(f"Unsupported artifact filename: {filename}")


def pypi_release_file(project_name: str, version: str, filename: str) -> dict[str, str]:
    """Resolve the source URL and SHA for an exact artifact filename from PyPI."""
    request = Request(
        f"https://pypi.org/pypi/{project_name}/{version}/json",
        headers={"User-Agent": PYPI_USER_AGENT},
    )
    with urlopen(request) as response:
        data = json.load(response)

    for release_file in data.get("urls", []):
        if release_file.get("filename") != filename:
            continue
        return {
            "name": str(data.get("info", {}).get("name") or project_name),
            "url": str(release_file["url"]),
            "sha256": str(release_file["digests"]["sha256"]),
            "filename": str(release_file["filename"]),
            "packagetype": str(release_file["packagetype"]),
        }

    raise ValueError(f"Could not find {filename} in PyPI metadata for {project_name} {version}")


def resolve_runtime_resources(
    requirements: list[str],
    *,
    python_executable: str,
) -> list[dict[str, str]]:
    """Resolve the fully pinned Homebrew resource list for BatLLM's runtime dependencies."""
    with tempfile.TemporaryDirectory(prefix="batllm-homebrew-") as temp_dir_raw:
        temp_dir = Path(temp_dir_raw)
        command = [
            python_executable,
            "-m",
            "pip",
            "download",
            "--disable-pip-version-check",
            "--dest",
            str(temp_dir),
            "--only-binary=:all:",
            *(f"--no-binary={package_name}" for package_name in SOURCE_ONLY_PACKAGES),
            *(requirements + EXTRA_BUILD_REQUIREMENTS),
        ]
        subprocess.run(command, cwd=ROOT, check=True)

        resources: list[dict[str, str]] = []
        for artifact_path in sorted(temp_dir.iterdir(), key=lambda path: path.name.casefold()):
            if not artifact_path.is_file():
                continue
            project_name, version = parse_downloaded_artifact_name(artifact_path.name)
            resources.append(pypi_release_file(project_name, version, artifact_path.name))

    return sorted(resources, key=lambda resource: resource["name"].casefold())


def git_ls_files(*args: str) -> list[Path]:
    """Return git-tracked or untracked file paths relative to the repository root."""
    proc = subprocess.run(
        ["git", "ls-files", *args, "-z"],
        cwd=ROOT,
        capture_output=True,
        text=False,
        check=True,
    )
    entries = [entry.decode("utf-8") for entry in proc.stdout.split(b"\0") if entry]
    return [ROOT / entry for entry in entries]


def create_worktree_archive(output_path: Path, *, prefix: str = "BatLLM") -> Path:
    """Create a tar.gz archive from the current worktree, including untracked files."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    candidates = git_ls_files() + git_ls_files("--others", "--exclude-standard")
    seen: set[Path] = set()

    with tarfile.open(output_path, "w:gz") as archive:
        for candidate in sorted(candidates, key=lambda path: str(path).casefold()):
            if candidate in seen or not candidate.is_file():
                continue
            seen.add(candidate)
            archive.add(candidate, arcname=f"{prefix}/{candidate.relative_to(ROOT)}")

    return output_path


def github_archive_url(*, owner: str, repo: str, tag: str | None = None, branch: str | None = None) -> str:
    """Build a GitHub archive URL for a tag or branch."""
    if bool(tag) == bool(branch):
        raise ValueError("Provide exactly one of tag or branch.")
    if tag:
        return f"https://github.com/{owner}/{repo}/archive/refs/tags/{tag}.tar.gz"
    return f"https://github.com/{owner}/{repo}/archive/refs/heads/{branch}.tar.gz"


def render_formula(
    *,
    version: str,
    source_url: str,
    source_sha256: str,
    resources: list[dict[str, str]],
) -> str:
    """Render the Homebrew formula text."""
    def resource_filename(resource: dict[str, str]) -> str:
        return str(resource.get("filename") or Path(resource["url"]).name)

    wheel_resource_names = [
        resource["name"]
        for resource in resources
        if resource_filename(resource).endswith(".whl")
    ]
    sdist_resource_names = [
        resource["name"]
        for resource in resources
        if not resource_filename(resource).endswith(".whl")
    ]
    resource_blocks = "\n\n".join(
        (
            f'  resource "{resource["name"]}" do\n'
            f'    url "{resource["url"]}"\n'
            f'    sha256 "{resource["sha256"]}"\n'
            "  end"
        )
        for resource in resources
    )
    wheel_install_block = "\n".join(
        (
            f'    resource("{resource_name}").stage do\n'
            f'      venv.pip_install Pathname.pwd/resource("{resource_name}").downloader.basename\n'
            '    end'
        )
        for resource_name in wheel_resource_names
    )
    sdist_install_block = "\n".join(
        (
            f'    venv.pip_install resource("{resource_name}"), build_isolation: false'
            if resource_name == "pydantic_core"
            else f'    venv.pip_install resource("{resource_name}")'
        )
        for resource_name in sdist_resource_names
    )
    return (
        'class Batllm < Formula\n'
        '  include Language::Python::Virtualenv\n\n'
        '  desc "AI-mediated local battle game powered by Ollama"\n'
        '  homepage "https://github.com/krahd/BatLLM"\n'
        f'  url "{source_url}"\n'
        f'  sha256 "{source_sha256}"\n'
        '  license "MIT"\n'
        f'  version "{version}"\n\n'
        '  depends_on "ollama"\n'
        '  depends_on "python@3.12"\n'
        '  depends_on "rust" => :build\n'
        '  depends_on "sdl2"\n'
        '  depends_on "sdl2_image"\n'
        '  depends_on "sdl2_mixer"\n'
        '  depends_on "sdl2_ttf"\n\n'
        f'{resource_blocks}\n\n'
        '  def install\n'
        '    odie "BatLLM Homebrew packaging currently supports macOS on Apple Silicon only." unless OS.mac? && Hardware::CPU.arm?\n\n'
        '    venv = virtualenv_create(libexec/"venv", "python3.12")\n'
        f'{wheel_install_block}\n'
        '    ENV.prepend_path "PATH", libexec/"venv/bin"\n'
        f'{sdist_install_block}\n\n'
        '    pkgshare.install Dir["*"]\n\n'
        '    (bin/"batllm").write <<~SH\n'
        '      #!/usr/bin/env bash\n'
        '      set -euo pipefail\n'
        '      export BATLLM_HOME="${BATLLM_HOME:-$HOME/Library/Application Support/BatLLM}"\n'
        '      mkdir -p "$BATLLM_HOME"\n'
        '      export PATH="#{Formula["ollama"].opt_bin}:$PATH"\n'
        '      exec "#{libexec}/venv/bin/python" "#{pkgshare}/run_batllm.py" "$@"\n'
        '    SH\n\n'
        '    (bin/"batllm-analyzer").write <<~SH\n'
        '      #!/usr/bin/env bash\n'
        '      set -euo pipefail\n'
        '      export BATLLM_HOME="${BATLLM_HOME:-$HOME/Library/Application Support/BatLLM}"\n'
        '      mkdir -p "$BATLLM_HOME"\n'
        '      export PATH="#{Formula["ollama"].opt_bin}:$PATH"\n'
        '      exec "#{libexec}/venv/bin/python" "#{pkgshare}/run_game_analyzer.py" "$@"\n'
        '    SH\n'
        '  end\n\n'
        '  test do\n'
        '    ENV["BATLLM_HOME"] = (testpath/"batllm-home").to_s\n'
        '    ENV["KIVY_HOME"] = (testpath/"kivy-home").to_s\n'
        '    ENV["KIVY_NO_ARGS"] = "1"\n'
        '    ENV["KIVY_WINDOW"] = "mock"\n\n'
        '    system libexec/"venv/bin/python", "-c", <<~PY\n'
        '      import sys\n'
        '      sys.path.insert(0, "#{pkgshare}/src")\n'
        '      from configs.app_config import AppConfig\n'
        '      from util.paths import resolve_saved_sessions_dir\n'
        '      config = AppConfig()\n'
        '      assert config.get("llm", "model") == "smollm2"\n'
        '      saved_dir = resolve_saved_sessions_dir("saved_sessions")\n'
        '      assert saved_dir.name == "saved_sessions"\n'
        '      print("batllm-homebrew-ok")\n'
        '    PY\n'
        '  end\n'
        'end\n'
    )


def write_formula(path: Path, contents: str) -> None:
    """Write the rendered formula to disk."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(contents, encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    """Create the CLI parser for the Homebrew formula generator."""
    parser = argparse.ArgumentParser(description="Generate a Homebrew formula for BatLLM")
    parser.add_argument(
        "--formula-out",
        type=Path,
        default=DEFAULT_FORMULA_OUTPUT,
        help="Where to write the generated formula.",
    )
    parser.add_argument(
        "--python-executable",
        default=str(DEFAULT_PYTHON if DEFAULT_PYTHON.exists() else Path("python3")),
        help="Python executable to use for pip download resolution.",
    )
    parser.add_argument(
        "--github-tag",
        help="Published GitHub tag to use as the formula source archive, for example v0.3.0.",
    )
    parser.add_argument(
        "--github-branch",
        help="Published GitHub branch to use as the formula source archive.",
    )
    parser.add_argument(
        "--source-url",
        help="Explicit source tar.gz URL to embed in the formula.",
    )
    parser.add_argument(
        "--source-sha256",
        help="Explicit source archive SHA-256. If omitted for a URL source, the generator downloads and hashes it.",
    )
    parser.add_argument(
        "--source-archive",
        type=Path,
        help="Local source archive to embed as a file:// URL for local validation.",
    )
    parser.add_argument(
        "--create-worktree-archive",
        type=Path,
        help="Create a local source archive from the current worktree and use it as the formula source.",
    )
    parser.add_argument(
        "--version",
        default=read_version(),
        help="Version string to embed in the formula. Defaults to VERSION.",
    )
    return parser


def resolve_source(args: argparse.Namespace) -> tuple[str, str]:
    """Resolve the source URL and SHA for the generated formula."""
    if args.create_worktree_archive is not None:
        archive_path = create_worktree_archive(args.create_worktree_archive, prefix="BatLLM")
        return archive_path.resolve().as_uri(), sha256_file(archive_path)

    if args.source_archive is not None:
        archive_path = args.source_archive.resolve()
        return archive_path.as_uri(), sha256_file(archive_path)

    if args.source_url:
        sha256 = args.source_sha256 or sha256_url(args.source_url)
        return args.source_url, sha256

    if args.github_tag or args.github_branch:
        source_url = github_archive_url(
            owner=GITHUB_OWNER,
            repo=GITHUB_REPO,
            tag=args.github_tag,
            branch=args.github_branch,
        )
        sha256 = args.source_sha256 or sha256_url(source_url)
        return source_url, sha256

    raise SystemExit(
        "Provide one source selector: --github-tag, --github-branch, --source-url, --source-archive, or --create-worktree-archive."
    )


def main(argv: list[str] | None = None) -> int:
    """Generate the BatLLM Homebrew formula."""
    parser = build_parser()
    args = parser.parse_args(argv)
    requirements = read_requirements(HOMEBREW_REQUIREMENTS)
    source_url, source_sha256 = resolve_source(args)
    resources = resolve_runtime_resources(requirements, python_executable=args.python_executable)
    formula = render_formula(
        version=args.version,
        source_url=source_url,
        source_sha256=source_sha256,
        resources=resources,
    )
    write_formula(args.formula_out, formula)
    print(args.formula_out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())