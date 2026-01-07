import typing

from aiohttp import ClientWebSocketResponse, ClientSession


class WebsocketTransport:
    __slots__: tuple[str, ...] = ("connection",)

    @classmethod
    async def open(cls, url: str) -> typing.Self:
        session: ClientSession = ClientSession()
        connection: ClientWebSocketResponse = await session.ws_connect(
            url, max_msg_size=0
        )
        return cls(connection)

    def __init__(self, connection: ClientWebSocketResponse) -> None:
        self.connection = connection

    async def close(self) -> None: ...
