class WBError(Exception):
    ...


class WBAuthError(WBError):
    ...


class WBRateLimit(WBError):
    ...


class WBUnexpectedResponse(WBError):
    ...
