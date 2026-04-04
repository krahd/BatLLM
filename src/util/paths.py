"""Filesystem path helpers for BatLLM."""

from __future__ import annotations

from pathlib import Path

from kivy.resources import resource_add_path


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
ASSETS_DIR = SRC_DIR / "assets"
VIEW_DIR = SRC_DIR / "view"
GAME_DIR = SRC_DIR / "game"
DOCS_DIR = ROOT_DIR / "docs"


def repo_path(*parts: str) -> Path:
    """Return an absolute path inside the repository root."""
    return ROOT_DIR.joinpath(*parts)


def src_path(*parts: str) -> Path:
    """Return an absolute path inside ``src``."""
    return SRC_DIR.joinpath(*parts)


def asset_path(*parts: str) -> Path:
    """Return an absolute path inside ``src/assets``."""
    return ASSETS_DIR.joinpath(*parts)


def view_path(*parts: str) -> Path:
    """Return an absolute path inside ``src/view``."""
    return VIEW_DIR.joinpath(*parts)


def prompt_asset_dir() -> Path:
    """Return the prompt samples directory."""
    return asset_path("prompts")


def theme_colors_path() -> Path:
    """Return the path to the Kivy theme colour properties file."""
    return view_path("theme_colors.properties")


def resolve_repo_relative(path_like: str | Path) -> Path:
    """Resolve a config or resource path relative to the repository."""
    path = Path(path_like)
    if path.is_absolute():
        return path

    candidates = (
        ROOT_DIR / path,
        SRC_DIR / path,
    )
    for candidate in candidates:
        if candidate.exists():
            return candidate

    return ROOT_DIR / path


def resolve_saved_sessions_dir(folder_name: str | Path) -> Path:
    """Resolve the saved-sessions folder and ensure it exists."""
    path = Path(folder_name)
    if not path.is_absolute():
        path = ROOT_DIR / path
    path.mkdir(parents=True, exist_ok=True)
    return path


def register_kivy_resource_paths() -> None:
    """Register the app resource directories with Kivy."""
    for path in (
        SRC_DIR,
        ASSETS_DIR,
        ASSETS_DIR / "images",
        ASSETS_DIR / "sounds",
        VIEW_DIR,
        GAME_DIR,
    ):
        resource_add_path(str(path))
