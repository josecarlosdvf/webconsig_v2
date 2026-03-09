from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def run_step(command: list[str]) -> int:
    print(f"\n>> {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT)
    return result.returncode


def main() -> int:
    steps = [
        [sys.executable, "tools/architecture_guard.py"],
        [sys.executable, "tools/duplicate_guard.py"],
        [sys.executable, "tools/authz_guard.py"],
    ]

    for command in steps:
        code = run_step(command)
        if code != 0:
            return code

    print("\nGovernança: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
