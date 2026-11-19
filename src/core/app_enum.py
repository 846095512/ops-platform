from enum import Enum
from typing import NamedTuple


class BizVal(NamedTuple):
    code: int
    msg: str


class BizStatus(Enum):
    SUCCESS = BizVal(0, "Request Success")
    UNAUTHORIZED = BizVal(40001, "Request Unauthorized")
    FORBIDDEN = BizVal(40003, "Request Forbidden")
    PARAM_ERROR = BizVal(40000, "Request Parameter Error")
    NOT_FOUND = BizVal(40004, "Request Not Found")
    BIZ_ERROR = BizVal(50000, "Request Server Error")
    USER_NOT_FOUND = BizVal(500001, "Request User Not Found")

    @property
    def code(self) -> int:
        return self.value.code

    @property
    def msg(self) -> str:
        return self.value.msg
