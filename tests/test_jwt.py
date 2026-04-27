import time

import pytest

from skarner.core.auth import JWTDecodeError, JWTExpiredError, JWTManager


@pytest.fixture
def mgr():
    return JWTManager(secret="a-secret-key-that-is-long-enough-32b")


def test_encode_decode_roundtrip(mgr):
    payload = {"user_id": 1, "role": "admin"}
    token = mgr.encode(payload, expires_in=60)
    result = mgr.decode(token)
    assert result["user_id"] == 1
    assert result["role"] == "admin"


def test_exp_claim_is_set(mgr):
    token = mgr.encode({"user_id": 1}, expires_in=60)
    result = mgr.decode(token)
    assert "exp" in result
    assert result["exp"] > time.time()


def test_expired_token_raises(mgr):
    token = mgr.encode({"user_id": 1}, expires_in=-1)
    with pytest.raises(JWTExpiredError):
        mgr.decode(token)


def test_expired_is_subclass_of_decode_error(mgr):
    token = mgr.encode({"user_id": 1}, expires_in=-1)
    with pytest.raises(JWTDecodeError):
        mgr.decode(token)


def test_invalid_token_raises(mgr):
    with pytest.raises(JWTDecodeError):
        mgr.decode("not.a.valid.token")


def test_tampered_token_raises(mgr):
    token = mgr.encode({"user_id": 1}, expires_in=60)
    tampered = token[:-4] + "xxxx"
    with pytest.raises(JWTDecodeError):
        mgr.decode(tampered)


def test_wrong_secret_raises():
    token = JWTManager(secret="secret-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa").encode(
        {"user_id": 1}, expires_in=60
    )
    with pytest.raises(JWTDecodeError):
        JWTManager(secret="secret-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbb").decode(token)


def test_empty_secret_raises():
    with pytest.raises(ValueError):
        JWTManager(secret="")


def test_extra_claims_preserved(mgr):
    payload = {"user_id": 99, "scope": ["read", "write"], "meta": {"v": 1}}
    token = mgr.encode(payload, expires_in=60)
    result = mgr.decode(token)
    assert result["scope"] == ["read", "write"]
    assert result["meta"] == {"v": 1}
