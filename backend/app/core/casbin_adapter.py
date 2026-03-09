from __future__ import annotations

from collections.abc import Iterable

from casbin.persist import FilteredAdapter, load_policy_line
from sqlalchemy.orm import sessionmaker

from app.domain.models.access_control import CasbinRule


class SQLAlchemyCasbinAdapter(FilteredAdapter):
    def __init__(self, session_factory: sessionmaker):
        self.session_factory = session_factory
        self._filtered = False

    def is_filtered(self):
        return self._filtered

    def load_policy(self, model):
        self._filtered = False
        db = self.session_factory()
        try:
            for rule in db.query(CasbinRule).all():
                line = self._rule_to_line(rule)
                if line:
                    load_policy_line(line, model)
        finally:
            db.close()

    def save_policy(self, model):
        db = self.session_factory()
        try:
            db.query(CasbinRule).delete()
            db.flush()

            for sec in ("p", "g"):
                if sec not in model.model:
                    continue
                for ptype, assertion in model.model[sec].items():
                    for rule in assertion.policy:
                        db.add(self._line_to_rule(ptype, rule))

            db.commit()
            return True
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def add_policy(self, sec, ptype, rule):
        db = self.session_factory()
        try:
            db.add(self._line_to_rule(ptype, rule))
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def remove_policy(self, sec, ptype, rule):
        db = self.session_factory()
        try:
            q = db.query(CasbinRule).filter(CasbinRule.ptype == ptype)
            for idx, value in enumerate(rule[:6]):
                q = q.filter(getattr(CasbinRule, f"v{idx}") == value)
            q.delete()
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def remove_filtered_policy(self, sec, ptype, field_index, *field_values):
        db = self.session_factory()
        try:
            q = db.query(CasbinRule).filter(CasbinRule.ptype == ptype)
            for idx, value in enumerate(field_values):
                if value:
                    q = q.filter(getattr(CasbinRule, f"v{field_index + idx}") == value)
            removed = q.delete()
            db.commit()
            return removed > 0
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _line_to_rule(ptype: str, rule: Iterable[str]) -> CasbinRule:
        values = list(rule)
        return CasbinRule(
            ptype=ptype,
            v0=values[0] if len(values) > 0 else None,
            v1=values[1] if len(values) > 1 else None,
            v2=values[2] if len(values) > 2 else None,
            v3=values[3] if len(values) > 3 else None,
            v4=values[4] if len(values) > 4 else None,
            v5=values[5] if len(values) > 5 else None,
        )

    @staticmethod
    def _rule_to_line(rule: CasbinRule) -> str:
        values = [rule.v0, rule.v1, rule.v2, rule.v3, rule.v4, rule.v5]
        normalized = [value for value in values if value is not None]
        if not normalized:
            return ""
        return f"{rule.ptype}, " + ", ".join(normalized)
