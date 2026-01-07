from msgspec import Struct


class ReadyEvent(Struct):
    resume_gateway_url: str
    session_id: str
