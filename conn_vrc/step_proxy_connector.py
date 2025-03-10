import logging
import socket
from collections import deque
import asyncio
from pubsub import pub
import threading
from vrc_connector import VRCConnector

class StepProxyConnector(VRCConnector):
        
    RTDE_FREQ = 100
    REFRESH_RATES = 1 #RTDE_FREQ / 20 # default
    IDLE_TIME = (1.0 / float(RTDE_FREQ))
   
    def __init__(self, opcua_conn, opcuasettings, host = "127.0.0.1", port = 8080, freq = 60):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)
            
    async def listen(self):
        
        self.socket.settimeout(10)

        cnt = 0

        mesgSize = 25
        data = self.socket.recv(mesgSize)

        while self.STOP_SERVER is False:
            try:
                if True:
                    data = self.socket.recv(mesgSize)
                    if self.USE_QUEUE:
                        if cnt % int(self.REFRESH_RATES) == 0:
                            self.dqueue.append(data)
                    else:
                        await self.publish(data)

                #await self.idle()
                cnt += 1
            except Exception as e:
                logging.error('socket receiving exception')
                self.connect()

# if __name__ == '__main__':
#     vrc_conn = SiasunConnector()

#     SiasunConnector.run_vrc_server_thread(vrc_conn)