#!/usr/bin/env python3
"""Read-only audit before standardizing AI_MR_Sandbox chapter Markdown names.

Usage from repository root:
    py -3.11 .\bootstrap\audit_chapter_renames.py

This script does not create/modify files or change Git state.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path


RENAMES = [
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
]


def git_output(root: Path, *args: str) -> tuple[int, str]:
    try:
        p = subprocess.run(
            ["git", "-c", f"safe.directory={root.as_posix()}", "-C", str(root), *args],
            capture_output=True, text=True, encoding="utf-8", errors="replace", check=False,
        )
        return p.returncode, p.stdout
    except OSError:
        return -1, ""


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    documents = root / "documents"
    if not documents.is_dir():
        print(f"ERROR: documents directory not found: {documents}")
        return 2

    print("=== CH01-CH10 chapter rename audit (READ ONLY) ===")
    print(f"Repository: {root}")
    code, branch = git_output(root, "branch", "--show-current")
    print(f"Git branch: {branch.strip() if code == 0 else 'UNKNOWN'}")
    _, status = git_output(root, "status", "--short")
    if status.strip():
        print("Git status (existing changes; NOT modified by this audit):")
        for line in status.splitlines()[:40]:
            print(f"  {line}")
        if len(status.splitlines()) > 40:
            print("  ...")
    else:
        print("Git worktree: CLEAN")

    print("\nPlanned renames (documents/ only):")
    problems: list[str] = []
    for old, new in RENAMES:
        source, dest = documents / old, documents / new
        state = "OK"
        if not source.is_file():
            state = "MISSING SOURCE"
            problems.append(f"Missing: {source}")
        if dest.exists():
            state = "TARGET EXISTS"
            problems.append(f"Target already exists: {dest}")
        print(f"  {old}  ->  {new}  [{state}]")

    # Find *filename mentions*, not generic CHECKPOINT-N historical wording.
    # Also include a known misspelling of the old CH10.7 filename.
    names = [old for old, _ in RENAMES] + ["CHECKPOINT-9.md", "CP10.7_InstallImageLeartning.md"]
    patterns = [(name, re.compile(re.escape(name), re.IGNORECASE)) for name in names]
    code, tracked = git_output(root, "ls-files", "-z")
    # NUL is preserved in stdout; inspect only tracked, text-like files.
    paths = [root / p for p in tracked.split("\0") if p] if code == 0 else []
    extensions = {".md", ".ps1", ".py", ".cmd", ".bat", ".json", ".txt", ".yml", ".yaml"}
    hits: list[tuple[str, int, str, str]] = []
    for path in paths:
        if path.suffix.lower() not in extensions or not path.is_file():
            continue
        try:
            if path.stat().st_size > 3_000_000:
                continue
            content = path.read_text(encoding="utf-8-sig")
        except (OSError, UnicodeError):
            continue
        rel = path.relative_to(root).as_posix()
        for lineno, line in enumerate(content.splitlines(), 1):
            for name, pattern in patterns:
                if pattern.search(line):
                    hits.append((rel, lineno, name, line.strip()))
    print(f"\nFilename references in Git-tracked text files: {len(hits)}")
    print("  (Some mentions are historical prose, NOT links; do not replace blindly.)")
    for rel, lineno, name, line in hits[:50]:
        excerpt = line[:170] + ("..." if len(line) > 170 else "")
        print(f"  {rel}:{lineno} [{name}] {excerpt}")
    if len(hits) > 50:
        print(f"  ... {len(hits) - 50} further reference matches omitted")
    print("\nAdditional checks:")
    for name in ["CH09-MREALIntegration.md", "CH11-DemoReproduction.md"]:
        print(f"  {name}: {'PRESENT' if (documents / name).is_file() else 'MISSING'}")
    print(f"  python/CHECKPOINT-9.md: {'PRESERVED' if (root / 'python' / 'CHECKPOINT-9.md').is_file() else 'NOT FOUND'}")
    print("\nPREVIEW ONLY: No files or Git index entries were modified.")
    if problems:
        print("BLOCKERS:")
        for problem in problems:
            print(f"  {problem}")
        return 2
    print("Ready for a separately reviewed migration plan. No renames executed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
