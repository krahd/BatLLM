from __future__ import annotations

import tarfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

from util import packaging_smoke


def test_required_members_for_platform_bundles_include_analyzer_launchers() -> None:
    assert "run-game-analyzer.bat" in packaging_smoke.required_members_for_artifact(
        "BatLLM-v0.3.4-windows.zip"
    )
    assert "run-game-analyzer.command" in packaging_smoke.required_members_for_artifact(
        "BatLLM-v0.3.4-macos.zip"
    )
    assert "run-game-analyzer.sh" in packaging_smoke.required_members_for_artifact(
        "BatLLM-v0.3.4-linux.tar.gz"
    )


def test_missing_required_members_detects_missing_files_in_zip(tmp_path: Path) -> None:
    archive_path = tmp_path / "bundle.zip"
    with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
        archive.writestr("BatLLM-v0.3.4-windows/run-batllm.bat", "echo ok")

    missing = packaging_smoke.missing_required_members(
        archive_path,
        ("run-batllm.bat", "run-game-analyzer.bat"),
    )

    assert missing == ["run-game-analyzer.bat"]


def test_missing_required_members_detects_missing_files_in_tar(tmp_path: Path) -> None:
    stage = tmp_path / "stage"
    stage.mkdir(parents=True, exist_ok=True)
    (stage / "run-batllm.sh").write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    archive_path = tmp_path / "bundle.tar.gz"
    with tarfile.open(archive_path, "w:gz") as archive:
        archive.add(stage / "run-batllm.sh", arcname="BatLLM-v0.3.4-linux/run-batllm.sh")

    missing = packaging_smoke.missing_required_members(
        archive_path,
        ("run-batllm.sh", "run-game-analyzer.sh"),
    )

    assert missing == ["run-game-analyzer.sh"]


def test_expected_release_artifact_paths_uses_versioned_dist_layout(tmp_path: Path) -> None:
    paths = packaging_smoke.expected_release_artifact_paths(tmp_path, "0.3.4")

    assert paths["source_zip"] == tmp_path / "dist" / "releases" / "BatLLM-v0.3.4-source.zip"
    assert paths["linux_tgz"] == tmp_path / "dist" / "releases" / "BatLLM-v0.3.4-linux.tar.gz"
