from __future__ import annotations

from collections import defaultdict
from hashlib import sha256
from pathlib import Path
import sys

ROOTS = [
    Path(__file__).resolve().parents[2] / "backend" / "app",
    Path(__file__).resolve().parents[2] / "frontend" / "src",
]

SKIP_NAMES = {"__init__.py"}


def main() -> int:
    fingerprints: dict[str, list[Path]] = defaultdict(list)

    for root in ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if not path.is_file() or path.name in SKIP_NAMES:
                continue
            content = path.read_bytes()
            digest = sha256(content).hexdigest()
            fingerprints[digest].append(path)

    duplicates = [group for group in fingerprints.values() if len(group) > 1]
    if duplicates:
        print("Arquivos duplicados detectados:")
        for group in duplicates:
            print(" - grupo:")
            for path in group:
                print(f"   * {path}")
        return 1

    print("Duplicação de arquivos: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
