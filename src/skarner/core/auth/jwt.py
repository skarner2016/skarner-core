from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

__all__ = ["JWTManager", "JWTDecodeError", "JWTExpiredError"]


class JWTDecodeError(Exception):
    pass


class JWTExpiredError(JWTDecodeError):
    pass


class JWTManager:
    def __init__(self, secret: str, algorithm: str = "HS256") -> None:
        if not secret:
            raise ValueError("secret must not be empty")
        self._secret = secret
        self._algorithm = algorithm

    def encode(self, payload: dict[str, Any], expires_in: int) -> str:
        """Sign a payload and return a JWT string.

        Args:
            payload: Claims to include in the token.
            expires_in: Token lifetime in seconds.
        """
        data = payload.copy()
        data["exp"] = datetime.now(tz=timezone.utc) + timedelta(seconds=expires_in)
        return jwt.encode(data, self._secret, algorithm=self._algorithm)

    def decode(self, token: str) -> dict[str, Any]:
        """Verify and decode a JWT string.

        Raises:
            JWTExpiredError: Token has expired.
            JWTDecodeError: Token is invalid.
        """
        try:
            return jwt.decode(token, self._secret, algorithms=[self._algorithm])
        except jwt.ExpiredSignatureError as e:
            raise JWTExpiredError("token has expired") from e
        except jwt.PyJWTError as e:
            raise JWTDecodeError(f"invalid token: {e}") from e
