"""Filesystem path helpers for BatLLM."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from kivy.resources import resource_add_path


ROOT_DIR = Path(__file__).resolve().parents[2]
SRC_DIR = ROOT_DIR / "src"
ASSETS_DIR = SRC_DIR / "assets"
VIEW_DIR = SRC_DIR / "view"
GAME_DIR = SRC_DIR / "game"
DOCS_DIR = ROOT_DIR / "docs"
BATLLM_HOME_ENV = "BATLLM_HOME"


def repo_path(*parts: str) -> Path:
    """Return an absolute path inside the repository root."""
    return ROOT_DIR.joinpath(*parts)


def configured_batllm_home() -> Path | None:
    """Return the user-writable BatLLM home directory, when explicitly configured."""
    configured = os.environ.get(BATLLM_HOME_ENV, "").strip()
    if not configured:
        return None
    return Path(configured).expanduser()


def default_batllm_home() -> Path:
    """Return the default user-writable BatLLM home for the current platform."""
    home = Path.home()
    if sys.platform == "darwin":
        return home / "Library" / "Application Support" / "BatLLM"
    if os.name == "nt":
        appdata = os.environ.get("APPDATA", "").strip()
        if appdata:
            return Path(appdata) / "BatLLM"
        return home / "AppData" / "Roaming" / "BatLLM"
    return home / ".local" / "share" / "BatLLM"


def active_batllm_home() -> Path | None:
    """Return the active BatLLM home when packaged installs opt into a writable location."""
    configured = configured_batllm_home()
    if configured is not None:
        return configured
    return None


def resolve_config_path(default_path: Path | None = None) -> Path:
    """Return the mutable runtime config path for the current process."""
    home_dir = active_batllm_home()
    if home_dir is not None:
        return home_dir / "config.yaml"
    if default_path is not None:
        return default_path
    return SRC_DIR / "configs" / "config.yaml"


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
        home_dir = active_batllm_home()
        if home_dir is not None:
            path = home_dir / path
        else:
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
