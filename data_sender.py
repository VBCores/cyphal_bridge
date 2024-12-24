import sys
import select
import asyncio
import os

import pycyphal
import pycyphal.application
import uavcan.node
import uavcan.si.unit.angle
import uavcan.si.unit.angular_velocity
import uavcan.si.unit.voltage

from pycyphal.application import make_transport
from pycyphal.application.register import Natural16, Natural32, ValueProxy
from pycyphal.transport.can.media.socketcan import SocketCANMedia
from pycyphal.transport.can import CANTransport

import random

class Sender:
    def __init__(self, port, register_file_name="sender.db") -> None:
        self.REGISTER_FILE = register_file_name
        node_info = uavcan.node.GetInfo_1.Response(
            software_version=uavcan.node.Version_1(major=1, minor=0),
            name="org.voltbro.data_sender",
        )
        self._node = pycyphal.application.make_node(
            node_info,
            self.REGISTER_FILE,
            transport=make_transport(
                {
                    "uavcan.can.iface": ValueProxy("socketcan:can1"),
                    "uavcan.node.id": ValueProxy(Natural16([3])),
                    "uavcan.can.mtu": ValueProxy(Natural16([64])),
                    "uavcan.can.bitrate": ValueProxy(Natural32([500000, 4000000])),
                }
            ),
        )
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = os.getpid() % 100

        self.data = 0
        self.port = port
        
        self.__data_from_subscribers = {}
        self.subs = []
        self.publisher = self._node.make_publisher(uavcan.si.unit.angular_velocity.Scalar_1, int(self.port))
        #self.is_cyphal_on = True

    def start(self):
        self._node.start()

    def close(self) -> None:
        self._node.close()
        #self.is_cyphal_on = False


    def set_data(self, data):
        self.data = data

    async def pub_data(self):
        await self.publisher.publish(uavcan.si.unit.angular_velocity.Scalar_1(self.data))

    async def pub_heartbeat(self):
        self._node.heartbeat_publisher._uptime = self._uptime
        self._uptime += 1
        self._node.heartbeat_publisher.make_message()




async def main():
    sender = Sender(input("port: "))
    sender.start()
    print('Created sender')
    
    try:
        while True:
            i, o, e = select.select( [sys.stdin], [], [], 0.5 )
            if i:
                value = sys.stdin.readline().strip()
                print(f"Sending {value}")
                data = int(value)
                sender.set_data(data)
                await sender.pub_data()
                print("data published ", data)
            await asyncio.sleep(0.01)
    except KeyboardInterrupt:
        sender.close()  


if __name__ == "__main__":
    asyncio.run(main())
