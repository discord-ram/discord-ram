import msgspec

from ram.gateway.op_code import OpCode


class GatewayPayload(msgspec.Struct):
    op: OpCode
    data: object | None = msgspec.field(default=None, name="d")
