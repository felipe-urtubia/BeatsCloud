#!/usr/bin/env python3
"""Keep technical QA logs private and hide common credentials from them."""

from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path


SECRET_PATTERNS = [
    (re.compile(r"(?i)(password|passwd|secret|token|api[_ -]?key)(\s*[=:]\s*)([^\s,;]+)"), r"\1\2[redactado]"),
    (re.compile(r"(?i)(authorization:\s*bearer\s+)[A-Za-z0-9._~+/=-]+"), r"\1[redactado]"),
    (re.compile(r"(?i)(authorization:\s*token\s+)[A-Za-z0-9._~+/=-]+"), r"\1[redactado]"),
    (re.compile(r"(?i)(postgres(?:ql)?://[^:/\s]+:)[^@/\s]+(@)"), r"\1[redactado]\2"),
    (re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"), "[token JWT redactado]"),
    (re.compile(r"(?i)(https?://[^\s?]+)\?[^\s]+"), r"\1?[parámetros firmados redactados]"),
]
ACCOUNT_PASSWORD = re.compile(
    r"(?i)(temporary password[^:]*:|password(?:\s+for\s+[^:]+)?:)\s*(\S+)"
)
QA_ACCOUNT_PASSWORD = re.compile(r"(?i)^((?:qa-[a-z0-9_-]+|demo-productor)\s*:\s*)\S+(.*)$")


def redact(line: str) -> str:
    if "-----BEGIN " in line and "PRIVATE KEY-----" in line:
        return "[contenido de clave privada redactado]\n"
    line = ACCOUNT_PASSWORD.sub(r"\1 [redactado]", line)
    line = QA_ACCOUNT_PASSWORD.sub(r"\1[redactado]\2", line)
    for pattern, replacement in SECRET_PATTERNS:
        line = pattern.sub(replacement, line)
    return line


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("log_path", type=Path)
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--summary", action="store_true")
    args = parser.parse_args()
    args.log_path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(args.log_path.parent, 0o700)
    with args.log_path.open("a", encoding="utf-8", errors="replace") as log:
        os.chmod(args.log_path, 0o600)
        for raw in sys.stdin:
            safe = redact(raw)
            log.write(safe)
            log.flush()
            # The summary filter keeps terminal output short; raw sensitive lines are never echoed.
            if not args.quiet and (
                not args.summary
                or re.search(
                    r"(?i)^\s*(?:ERROR\b|FAILED\b|FAILURE\b|WARNING\b|Ran \d+ tests?\b|# (?:tests|pass|fail)\b|QA smoke\b|System check identified no issues\b|No changes detected\b|Traceback \()",
                    safe,
                )
            ):
                # Never echo raw lines that were redacted; credentials stay off screen and disk.
                sys.stdout.write(safe)
                sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
