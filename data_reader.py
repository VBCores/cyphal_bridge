import asyncio
import os

import pycyphal
import pycyphal.application
import uavcan.node
import uavcan.si.sample.angle
import uavcan.si.sample.angular_velocity
import uavcan.si.unit.voltage


class Reader:
     REGISTER_FILE = ""
     def __init__(self, register_file_name="reader.db") -> None:

        Reader.REGISTER_FILE = register_file_name 
        node_info = uavcan.node.GetInfo_1.Response(
            software_version=uavcan.node.Version_1(major=1, minor=0),
            name="org.voltbro.reader",
        )
        self._node = pycyphal.application.make_node(node_info, Reader.REGISTER_FILE)
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = os.getpid() % 100
        
        self.__data_from_subscribers = {}
        self.subs = []
        self.tasks = []
        self._node.start()

     def close(self) -> None:
        self._node.close()

     def add_sub(self, types, ids, timeout):
          if len(types) != len(ids):
               raise ValueError("Failed! The size of the types is not equal to the size of the IDs")
          else:
               for i in range(len(types)):
                    sub = self._node.make_subscriber(types[i], ids[i]) 
                    self.subs.append(sub)
                    self.tasks.append(asyncio.create_task(sub.receive_for(timeout)))

     def get_data(self):
          return self.__data_from_subscribers

     async def read(self):
          if not self.subs:
               raise ConnectionError("There are no subscribers") 
          messages = await asyncio.gather(*self.tasks)
          for i, msg in enumerate(messages):
               if msg is not None:
                    self.__data_from_subscribers[self.subs[i].transport_session.specifier.data_specifier.subject_id] = msg[0]
               else: 
                    self.__data_from_subscribers[self.subs[i].transport_session.specifier.data_specifier.subject_id] = None


async def main():
    reader = Reader()
    print('Created reader')
    reader.add_sub([uavcan.si.sample.angular_velocity.Scalar_1, uavcan.si.sample.angular_velocity.Scalar_1, 
                    uavcan.si.sample.angle.Scalar_1], [1111, 1112, 1113], 1)
    print('subscribers added')
    
    await reader.read()
    print('Data readed with timeout 1s')
    print(reader.get_data())    
    data = reader.get_data()
    print(data[1111].radian_per_second, data[1112].radian_per_second, data[1113].radian)
    reader.close()
    print('Closed')


if __name__ == "__main__":
    asyncio.run(main())
