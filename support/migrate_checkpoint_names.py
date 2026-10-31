#!/usr/bin/env python3
r"""Preview or safely stage chapter document renames for AI_MR_Sandbox.

Usage:
    py -3.11 .\bootstrap\migrate_checkpoint_names.py
    py -3.11 .\bootstrap\migrate_checkpoint_names.py --apply

No third-party Python packages. Historical prose and the python/CHECKPOINT-9.md
archive are deliberately untouched. Requires a clean *tracked* Git index and
working tree for --apply. Untracked helper scripts are allowed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

RENAMES = (
    ("CHECKPOINT-1.md", "CH01-SpeechToUnityConsole.md"),
    ("CHECKPOINT-1.1.md", "CH01.1-SpeechToUnityUI.md"),
    ("CHECKPOINT-2.md", "CH02-NaturalLanguageCommand.md"),
    ("CHECKPOINT-3.md", "CH03-BodyCenteredAction.md"),
    ("CHECKPOINT-4.md", "CH04-ActionVerification.md"),
    ("CHECKPOINT-5.md", "CH05-ExperienceLogging.md"),
    ("CHECKPOINT-6.md", "CH06-PermissionControl.md"),
    ("CHECKPOINT-7.md", "CH07-HumanEvaluation.md"),
    ("CHECKPOINT-8.md", "CH08-AIRManagerIntegration.md"),
    ("CHECKPOINT-10.md", "CH10-PhysicalSpaceTracking.md"),
    ("CP-10.5_InstallLocalLLM.md", "CH10.5-LocalLLM.md"),
    ("CP10.6_InstallImageGeneration.md", "CH10.6-ImageGeneration.md"),
    ("CP10.7_InstallImageLearning.md", "CH10.7-ImageLearning.md"),
)

# Only operational file references are rewritten. Historical chapter labels,
# example transcripts, and old guide instructions stay as a historical record.
# Each count is asserted, to avoid silently changing an unexpected revision.
LINK_UPDATES = (
    ("IMAGE_LEARNING_GUI_SETUP.md", "CP10.6_InstallImageGeneration.md", "CH10.6-ImageGeneration.md", 1),
    ("IMAGE_LEARNING_GUI_SETUP.md", "CP10.7_InstallImageLearning.md", "CH10.7-ImageLearning.md", 1),
    ("documents/CP10.6_InstallImageGeneration.md", "CP10.7_InstallImageLeartning.md", "CH10.7-ImageLearning.md", 2),
    ("documents/CP10.7_InstallImageLearning.md", "CP10.6_InstallImageGeneration.md", "CH10.6-ImageGeneration.md", 1),
)


def git(root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args],
        encoding="utf-8", errors="replace", capture_output=True, check=check,
    )


def require_git_clean(root: Path) -> None:
    # Check only tracked changes; helper scripts may be untracked.
    for args in (("diff", "--quiet"), ("diff", "--cached", "--quiet")):
        result = git(root, *args, check=False)
        if result.returncode != 0:
            raise ValueError("Tracked Git changes are present; commit or resolve them first.")


def replacement_bytes(raw: bytes, updates: list[tuple[str, str, int]], name: str) -> tuple[bytes, int]:
    # Preserve a UTF-8 BOM, and preserve the original newline bytes.
    bom = b"\xef\xbb\xbf"
    has_bom = raw.startswith(bom)
    try:
        content = raw[len(bom):].decode("utf-8") if has_bom else raw.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"Not UTF-8: {name}: {error}") from error
    total = 0
    for old, new, expected in updates:
        src, dst = f"`{old}`", f"`{new}`"
        count = content.count(src)
        if count != expected:
            raise ValueError(f"Unexpected reference count in {name}: {old}: expected {expected}, got {count}")
        content = content.replace(src, dst)
        total += count
    data = (bom if has_bom else b"") + content.encode("utf-8")
    return data, total


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true", help="Rename and stage the checked file changes")
    args = parser.parse_args()

    root = Path(__file__).resolve().parent.parent
    docdir = root / "documents"
    if not (root / ".git").exists():
        raise ValueError(f"Not a Git repository root: {root}")
    branch = git(root, "branch", "--show-current").stdout.strip()
    if branch != "portability-cleanup":
        raise ValueError(f"Unexpected Git branch: {branch!r} (expected portability-cleanup)")

    for required in ("documents/CH09-MREALIntegration.md", "documents/CH11-DemoReproduction.md", "python/CHECKPOINT-9.md"):
        if not (root / required).is_file():
            raise ValueError(f"Required preserved file missing: {required}")

    pairs: list[tuple[Path, Path]] = []
    for old, new in RENAMES:
        source, target = docdir / old, docdir / new
        if not source.is_file():
            raise ValueError(f"Source missing: {source}")
        if target.exists():
            raise ValueError(f"Target exists, refusing to overwrite: {target}")
        tracked = git(root, "ls-files", "--error-unmatch", "--", f"documents/{old}", check=False)
        if tracked.returncode != 0:
            raise ValueError(f"Source is not tracked by Git: {source}")
        pairs.append((source, target))

    changes: dict[Path, tuple[bytes, int]] = {}
    for file_name in sorted({entry[0] for entry in LINK_UPDATES}):
        source = root / file_name
        if not source.is_file():
            raise ValueError(f"Reference file missing: {file_name}")
        entries = [(old, new, count) for path, old, new, count in LINK_UPDATES if path == file_name]
        changes[source] = replacement_bytes(source.read_bytes(), entries, file_name)

    print(f"=== Chapter name migration ({'APPLY' if args.apply else 'PREVIEW'}) ===")
    print(f"Repository: {root}")
    print(f"Git branch: {branch}")
    print("Renames:")
    for source, target in pairs:
        print(f"  documents/{source.name} -> documents/{target.name}")
    print("Operational reference edits (only exact backticked filenames):")
    for file, (_, count) in changes.items():
        print(f"  {file.relative_to(root).as_posix()}: {count} occurrence(s)")
    print(f"Totals: {len(pairs)} renames; {sum(n for _, n in changes.values())} reference edits")
    print("Preserved: historical prose, python/CHECKPOINT-9.md, DOCX originals, PC environments")

    if not args.apply:
        print("PREVIEW ONLY: No files or Git index entries changed.")
        return 0

    require_git_clean(root)
    # All input validation is complete before any write. On an unexpected
    # filesystem/Git failure, inspect status and recover using Git history.
    for source, target in pairs:
        git(root, "mv", "--", f"documents/{source.name}", f"documents/{target.name}")
    rename_map = {source: target for source, target in pairs}
    updated_paths: list[str] = []
    for source, (data, _) in changes.items():
        destination = rename_map.get(source, source)
        destination.write_bytes(data)
        updated_paths.append(destination.relative_to(root).as_posix())
    git(root, "add", "--", *updated_paths)
    print("APPLIED: All renames and five operational reference edits staged, not committed.")
    print("Next inspect: git -c safe.directory=<repo> diff --cached --stat")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, subprocess.CalledProcessError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        if isinstance(exc, subprocess.CalledProcessError) and exc.stderr:
            print(exc.stderr, file=sys.stderr)
        sys.exit(1)
