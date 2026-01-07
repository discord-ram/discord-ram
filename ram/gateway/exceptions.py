class GatewayTransportClosed(Exception):
    __slots__: tuple[str, ...] = ("extra", "code")

    def __init__(
        self,
        *,
        code: int,
        extra: str | None,
    ) -> None:
        self.extra: str = extra or "No message"
        self.code = code


class GatewayShardStateConflict(Exception): ...
