from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Principal:
    subject: str
    username: str
    email: str | None
    roles: tuple[str, ...]
    groups: tuple[str, ...]
    authenticated: bool = False

    @property
    def actor(self) -> str:
        return self.username or "anonymous"


def anonymous_principal(actor: str = "anonymous") -> Principal:
    return Principal(
        subject=f"anonymous:{actor}",
        username=actor,
        email=None,
        roles=tuple(),
        groups=tuple(),
        authenticated=False,
    )


def principal_subjects(principal: Principal) -> str:
    subjects: list[str] = [f"user:{principal.username}"]
    subjects.extend(f"role:{role}" for role in principal.roles)
    subjects.extend(f"group:{group}" for group in principal.groups)
    return "|".join(sorted(set(subjects)))
