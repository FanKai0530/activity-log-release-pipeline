#!/usr/bin/env python3
"""Update the bounded README activity section from local Git history."""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import html
from pathlib import Path
import re
import subprocess
from urllib.parse import quote

START = "<!-- activity:start -->"
END = "<!-- activity:end -->"
GENERATED_PREFIX = "docs: update recent activity"


def validate_markers(text: str) -> tuple[int, int]:
    if text.count(START) != 1 or text.count(END) != 1:
        raise ValueError("README must contain exactly one activity start marker and one end marker")
    start = text.index(START) + len(START)
    end = text.index(END)
    if start >= end:
        raise ValueError("Activity markers must be in order on separate lines")
    if text[start:start + 1] not in ("\n", "\r") or text[end - 1:end] not in ("\n", "\r"):
        raise ValueError("Activity markers must be on separate lines")
    return start, end


def recent_commits(limit: int) -> list[tuple[str, str, str]]:
    result = subprocess.run(
        ["git", "log", "--format=%H%x1f%cs%x1f%s%x1e", "-n", str(max(30, limit * 4))],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    rows = []
    for record in result.stdout.split("\x1e"):
        fields = record.strip().split("\x1f")
        if len(fields) != 3:
            continue
        sha, date, subject = fields
        if subject.lower().startswith(GENERATED_PREFIX):
            continue
        rows.append((sha, date, subject))
        if len(rows) == limit:
            break
    return rows


def render_activity(commits: list[tuple[str, str, str]], repository: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
        raise ValueError("Repository must be in owner/name format")
    if not commits:
        return "_No commits are available yet._"
    lines = []
    for sha, date, subject in commits:
        if not re.fullmatch(r"[0-9a-f]{40}", sha):
            raise ValueError("Invalid commit SHA")
        datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        safe_subject = html.escape(subject, quote=False).replace("[", "&#91;").replace("]", "&#93;")
        url = f"https://github.com/{repository}/commit/{quote(sha)}"
        lines.append(f"- {date} · [{safe_subject}]({url}) (`{sha[:7]}`)")
    return "\n".join(lines)


def update(text: str, activity: str) -> str:
    start, end = validate_markers(text)
    newline = "\r\n" if "\r\n" in text else "\n"
    return text[:start] + newline + activity.replace("\n", newline) + newline + text[end:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--repository", required=True)
    parser.add_argument("--limit", type=int, default=8)
    parser.add_argument("--check", action="store_true", help="Validate markers without changing the file")
    parser.add_argument("--preview", action="store_true", help="Print proposed section without changing the file")
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error("--limit must be between 1 and 20")
    current = args.readme.read_text(encoding="utf-8")
    validate_markers(current)
    if args.check:
        print("Activity markers are valid")
        return 0
    activity = render_activity(recent_commits(args.limit), args.repository)
    new_text = update(current, activity)
    if args.preview:
        print(activity)
    elif new_text != current:
        args.readme.write_text(new_text, encoding="utf-8", newline="")
        print("README activity updated")
    else:
        print("README activity unchanged")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
