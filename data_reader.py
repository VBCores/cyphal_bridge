import pycyphal
import pycyphal.application
import uavcan.node
import asyncio
import os

import uavcan.si.sample.angle
import uavcan.si.sample.angular_velocity
import uavcan.si.unit.voltage


class Reader:
     REGISTER_FILE =  "reader.db"

     def __init__(self, _) -> None:
        node_info = uavcan.node.GetInfo_1.Response(
            software_version=uavcan.node.Version_1(major=1, minor=0),
            name="org.voltbro.reader",
        )
        self._node = pycyphal.application.make_node(node_info, Reader.REGISTER_FILE)
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = os.getpid() % 100
        
        self.d = {}
        self.subs = []
        self._node.start()

     def close(self) -> None:
        self._node.close()

     def add_sub(self, types, ids, n ):
          if len(types) != n or len(types) != n:
               print("Failed! Check size of ids and types")
          else:
               for i in range(n):
                    self.subs.append(self._node.make_subscriber(types[i], ids[i]))

     def get_data(self):
          return self.d

     async def read(self, timeout):
          if len(self.subs) != 0:
               for sub in self.subs:
                    msg = await sub.receive_for(timeout)
                    if msg is not None:
                         self.d[sub.transport_session.specifier.data_specifier.subject_id] = msg[0]
                    else: 
                         self.d[sub.transport_session.specifier.data_specifier.subject_id] = None


async def main():
    reader = Reader(None)
    print('Created reader')
    reader.add_sub([uavcan.si.sample.angular_velocity.Scalar_1, uavcan.si.sample.angular_velocity.Scalar_1, 
                    uavcan.si.sample.angle.Scalar_1], [1111, 1112, 1113], 3)
    print('subscribers added')
    
    await reader.read(1)
    print('Data readed with timeout 1s')
    print(reader.get_data())
    data = reader.get_data()
    print(data[1111].radian_per_second, data[1112].radian_per_second, data[1113].radian)
    reader.close()
    print('Closed')


if __name__ == "__main__":
    asyncio.run(main())
