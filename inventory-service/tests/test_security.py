import pytest
from fastapi import HTTPException

from inventory.security import _decode, create_token, hash_password, require_role, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse")
    assert verify_password("correct-horse", hashed)
    assert not verify_password("wrong-password", hashed)


def test_token_roundtrip():
    token = create_token("alice", "admin")
    principal = _decode(token)
    assert principal.username == "alice"
    assert principal.role == "admin"


def test_decode_rejects_garbage_token():
    with pytest.raises(HTTPException) as exc_info:
        _decode("not-a-real-token")
    assert exc_info.value.status_code == 401


def test_require_role_allows_matching_role():
    principal = _decode(create_token("bob", "field_tech"))
    dependency = require_role("field_tech", "admin")
    # The dependency's `principal` param defaults to a FastAPI Depends(...)
    # marker, but calling it with an explicit kwarg bypasses DI entirely.
    assert dependency(principal=principal) is principal


def test_require_role_rejects_other_role():
    principal = _decode(create_token("bob", "field_tech"))
    dependency = require_role("admin")
    with pytest.raises(HTTPException) as exc_info:
        dependency(principal=principal)
    assert exc_info.value.status_code == 403
