"""Business error exception class."""
from .codes import ErrorCode


class BusinessError(Exception):
    """业务异常基类。

    用于表示业务逻辑中的可预期错误，会被 FastAPI 异常处理器自动捕获并转换为标准响应格式。

    Example:
        >>> from skarner.core.exceptions import BusinessError, ErrorCode
        >>> raise BusinessError(ErrorCode.AUTH_INVALID_TOKEN, "Invalid credentials")
    """

    def __init__(self, code: ErrorCode, message: str):
        """初始化业务异常。

        Args:
            code: 错误码（ErrorCode 枚举值）
            message: 错误描述信息
        """
        self.code = code
        self.message = message
        super().__init__(f"{code.name}: {message}")
