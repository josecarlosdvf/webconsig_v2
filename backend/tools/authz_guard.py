from __future__ import annotations

from pathlib import Path
import re
import sys

ENDPOINTS_DIR = Path(__file__).resolve().parents[1] / "app" / "api" / "v1" / "endpoints"

IGNORE_FILES = {"health.py", "access_control.py", "__init__.py"}
ROUTE_DECORATOR_RE = re.compile(r"@router\.(get|post|put|patch|delete)\(")


def main() -> int:
    errors: list[str] = []

    for file in sorted(ENDPOINTS_DIR.glob("*.py")):
        if file.name in IGNORE_FILES:
            continue

        content = file.read_text(encoding="utf-8")
        has_http_route = bool(ROUTE_DECORATOR_RE.search(content))
        has_permission = "require_permission(" in content

        if has_http_route and not has_permission:
            errors.append(f"{file.name}: endpoints HTTP sem require_permission")

    if errors:
        print("Falhas de governança de autorização:")
        for error in errors:
            print(f" - {error}")
        return 1

    print("Autorização: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
