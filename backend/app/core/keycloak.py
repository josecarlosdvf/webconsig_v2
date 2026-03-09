from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
from jwt.algorithms import RSAAlgorithm
from fastapi import HTTPException, status

from app.core.config import settings
from app.core.security import Principal

_JWKS_CACHE: dict[str, Any] = {"expires_at": 0, "jwks": None}


def _realm_url() -> str:
    return f"{settings.keycloak_base_url.rstrip('/')}/realms/{settings.keycloak_realm}"


def _jwks_url() -> str:
    return f"{_realm_url()}/protocol/openid-connect/certs"


def _load_jwks() -> dict[str, Any]:
    now = int(time.time())
    cached = _JWKS_CACHE.get("jwks")
    expires_at = int(_JWKS_CACHE.get("expires_at") or 0)
    if cached and now < expires_at:
        return cached

    with httpx.Client(verify=settings.keycloak_verify_tls, timeout=10.0) as client:
        response = client.get(_jwks_url())
        response.raise_for_status()
        jwks = response.json()

    _JWKS_CACHE["jwks"] = jwks
    _JWKS_CACHE["expires_at"] = now + max(30, settings.keycloak_jwks_cache_seconds)
    return jwks


def _get_signing_key(token: str) -> Any:
    try:
        headers = jwt.get_unverified_header(token)
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido") from exc

    kid = headers.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido (kid ausente)")

    jwks = _load_jwks()
    for key in jwks.get("keys", []):
        if key.get("kid") == kid:
            return RSAAlgorithm.from_jwk(key)

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave pública do token não encontrada")


def decode_keycloak_token(token: str) -> dict[str, Any]:
    signing_key = _get_signing_key(token)
    issuer = _realm_url()

    try:
        claims = jwt.decode(
            token,
            signing_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
            issuer=issuer,
        )
        if settings.keycloak_client_id:
            token_aud = claims.get("aud")
            allowed = False
            if isinstance(token_aud, str):
                allowed = token_aud == settings.keycloak_client_id
            elif isinstance(token_aud, list):
                allowed = settings.keycloak_client_id in token_aud

            if not allowed:
                allowed = claims.get("azp") == settings.keycloak_client_id

            if not allowed:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token com client inválido")

        return claims
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido ou expirado") from exc


def principal_from_claims(claims: dict[str, Any]) -> Principal:
    preferred_username = str(claims.get("preferred_username") or claims.get("sub") or "anonymous")
    realm_roles = claims.get("realm_access", {}).get("roles", []) if isinstance(claims.get("realm_access"), dict) else []
    groups = claims.get("groups", []) if isinstance(claims.get("groups"), list) else []

    return Principal(
        subject=str(claims.get("sub") or preferred_username),
        username=preferred_username,
        email=claims.get("email"),
        roles=tuple(sorted({str(role) for role in realm_roles})),
        groups=tuple(sorted({str(group).strip("/") for group in groups if str(group).strip("/")})),
        authenticated=True,
    )
