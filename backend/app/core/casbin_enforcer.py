from __future__ import annotations

from threading import Lock

import casbin

from app.core.casbin_adapter import SQLAlchemyCasbinAdapter
from app.core.config import settings
from app.core.database import SessionLocal
from app.core.security import Principal, principal_subjects

_MODEL_TEXT = """
[request_definition]
r = subs, obj, act

[policy_definition]
p = priority, sub, obj, act, eft

[policy_effect]
e = priority(p.eft) || deny

[matchers]
m = hasSub(r.subs, p.sub) && regexMatch(r.obj, p.obj) && regexMatch(r.act, p.act)
"""

_LOCK = Lock()
_ENFORCER: casbin.Enforcer | None = None


def _has_sub(subjects: str, policy_subject: str) -> bool:
    return policy_subject in {item.strip() for item in subjects.split("|") if item.strip()}


def get_enforcer() -> casbin.Enforcer:
    global _ENFORCER
    if _ENFORCER is not None:
        return _ENFORCER

    with _LOCK:
        if _ENFORCER is not None:
            return _ENFORCER

        model = casbin.Model()
        model.load_model_from_text(_MODEL_TEXT)
        adapter = SQLAlchemyCasbinAdapter(SessionLocal)

        enforcer = casbin.Enforcer(model, adapter, enable_log=settings.app_debug)
        enforcer.add_function("hasSub", _has_sub)
        enforcer.enable_auto_save(True)
        enforcer.load_policy()

        if not enforcer.get_policy():
            enforcer.add_policy("10", "role:admin", ".*", ".*", "allow")
            enforcer.add_policy("20", "user:admin", ".*", ".*", "allow")

        _ENFORCER = enforcer
    return _ENFORCER


def reload_enforcer() -> None:
    enforcer = get_enforcer()
    enforcer.load_policy()


def enforce(principal: Principal, resource: str, action: str) -> bool:
    if not settings.authz_enabled:
        return True
    enforcer = get_enforcer()
    return bool(enforcer.enforce(principal_subjects(principal), resource, action))
