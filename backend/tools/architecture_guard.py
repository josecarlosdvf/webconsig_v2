from __future__ import annotations

import ast
from pathlib import Path
import sys

APP_ROOT = Path(__file__).resolve().parents[1] / "app"

GLOBAL_FORBIDDEN_IMPORTS: tuple[str, ...] = (
    "apps",
    "flask",
    "flask_login",
    "flask_wtf",
    "flask_sqlalchemy",
)

RULES: dict[str, tuple[str, ...]] = {
    "app.api.v1.endpoints": (
        "app.core.database",
        "app.domain.models",
    ),
    "app.application.services": (
        "app.api",
    ),
    "app.adapters.gateways": (
        "fastapi",
        "app.api",
    ),
}

ALLOW_EXCEPTIONS: dict[str, tuple[str, ...]] = {
    "app.api.v1.endpoints": (
        "sqlalchemy.orm",
        "app.adapters.gateways.audit_gateway",
    ),
}


def module_name_from_path(path: Path) -> str:
    rel = path.relative_to(APP_ROOT.parent)
    return ".".join(rel.with_suffix("").parts)


def imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                modules.add(node.module)
    return modules


def check_file(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    module_name = module_name_from_path(path)
    imports = imported_modules(tree)

    errors: list[str] = []

    if module_name.startswith("app."):
        for imported in imports:
            for blocked in GLOBAL_FORBIDDEN_IMPORTS:
                if imported == blocked or imported.startswith(blocked + "."):
                    errors.append(f"{module_name}: import legado proibido '{imported}'")

    for prefix, forbidden in RULES.items():
        if module_name.startswith(prefix):
            for imported in imports:
                allowed_prefixes = ALLOW_EXCEPTIONS.get(prefix, ())
                if any(imported == allowed or imported.startswith(allowed + ".") for allowed in allowed_prefixes):
                    continue
                for blocked in forbidden:
                    if imported == blocked or imported.startswith(blocked + "."):
                        errors.append(f"{module_name}: import proibido '{imported}' (regra: {prefix})")
    return errors


def main() -> int:
    files = [path for path in APP_ROOT.rglob("*.py") if path.name != "__init__.py"]
    all_errors: list[str] = []
    for path in files:
        all_errors.extend(check_file(path))

    if all_errors:
        print("Falhas de governança arquitetural:")
        for error in all_errors:
            print(f" - {error}")
        return 1

    print("Arquitetura: OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
