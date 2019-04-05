#
# This file is part of libottdadmin2
#
# License: http://creativecommons.org/licenses/by-nc-sa/3.0/
#

from asyncio import transports
from typing import Tuple, Any, Optional

from libottdadmin2.packets import AdminJoin, Packet, AdminQuit
from libottdadmin2.util import LoggableObject, camel_to_snake


class OttdClientMixIn(LoggableObject):
    def configure(self, password, user_agent=None, version=None):
        from libottdadmin2 import VERSION
        self._password = password
        self._user_agent = user_agent or "libottdadmin2"
        self._version = version or VERSION

    def connection_made(self, transport: transports.Transport = None) -> None:
        if transport:
            self.transport = transport
            self.peername = transport.get_extra_info("peername")

        self.log.info("Connection made to %s:%d", self.peername[0], self.peername[1])

        if self._password:
            self.log.info("Automatically authenticating: %s@%s", self._user_agent, self._version)
            self.send_packet(AdminJoin.create(password=self._password, name=self._user_agent, version=self._version))

    def data_received(self, data: bytes) -> None:
        self._buffer += data
        while True:
            found, length, packet = Packet.extract(self._buffer)
            self._buffer = self._buffer[length:]
            if not found:
                break
            self.packet_received(packet, packet.decode())

    def packet_received(self, packet: Packet, data: Tuple[Any, ...]):
        self.log.debug("Packet received: %r", data)
        funcname = "on_%s" % camel_to_snake(packet.__class__.__name__)
        handler = getattr(self, funcname, None)
        if handler and callable(funcname):
            handler(**data._asdict())

    def connection_closed(self):
        raise NotImplemented()

    def connection_lost(self, exc: Optional[Exception]) -> None:
        raise NotImplemented()

    def send_packet(self, packet: Packet):
        raise NotImplemented()

    def disconnect(self):
        self.send_packet(AdminQuit.create())
        self.connection_closed()


__all__ = [
    'OttdClientMixIn',
]