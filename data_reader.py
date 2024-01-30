import asyncio
import os

import pycyphal
import pycyphal.application
import uavcan.node
import uavcan.si.sample.angle
import uavcan.si.sample.angular_velocity
import uavcan.si.unit.voltage


class Reader:
     def __init__(self, register_file_name="reader.db") -> None:

        self.REGISTER_FILE = register_file_name 
        node_info = uavcan.node.GetInfo_1.Response(
            software_version=uavcan.node.Version_1(major=1, minor=0),
            name="org.voltbro.reader",
        )
        self._node = pycyphal.application.make_node(node_info, self.REGISTER_FILE)
        self._node.heartbeat_publisher.mode = uavcan.node.Mode_1.OPERATIONAL
        self._node.heartbeat_publisher.vendor_specific_status_code = os.getpid() % 100
        
        self.__data_from_subscribers = {}
        self.subs = []
        self._node.start()

     def close(self) -> None:
        self._node.close()

     def add_sub(self, subscribers):
          if not subscribers:
                    raise ValueError("Failed! Empty subscriber list")
          try:
               for sub in subscribers:
                    self.subs.append(self._node.make_subscriber(sub[0], sub[1]))
          except IndexError:
               raise ValueError("Failed! Subscribers must be a non-empty list of (type, id) tuples")

     def get_data(self):
          return self.__data_from_subscribers

     async def read(self, timeout):
          if not self.subs:
               raise ConnectionError("There are no subscribers") 
          tasks = (asyncio.create_task(sub.receive_for(timeout)) for sub in self.subs)
          messages = await asyncio.gather(*tasks)
          for i, msg in enumerate(messages):
               if msg is not None:
                    self.__data_from_subscribers[self.subs[i].transport_session.specifier.data_specifier.subject_id] = msg[0]
               else: 
                    self.__data_from_subscribers[self.subs[i].transport_session.specifier.data_specifier.subject_id] = None


async def main():
    reader = Reader()
    print('Created reader')
    reader.add_sub([(uavcan.si.sample.angular_velocity.Scalar_1, 1111), (uavcan.si.sample.angular_velocity.Scalar_1,  1112),
                    (uavcan.si.sample.angle.Scalar_1, 1113)])
    
    print('subscribers added')
    await reader.read(1)
    print('Data readed with timeout 1s')    
    data = reader.get_data()
    print(data[1111].radian_per_second, data[1112].radian_per_second, data[1113].radian)
    reader.close()
    print('Closed')


if __name__ == "__main__":
    asyncio.run(main())
