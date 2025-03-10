import logging
import socket
from collections import deque
import asyncio
from pubsub import pub
import threading

class VRCConnector:
        
    PORT = 2001        # UR RTDE PORT 
    RTDE_FREQ = 500 # UR RTDE frequency
    REFRESH_RATES = RTDE_FREQ / 20 # default
    IDLE_TIME = (1.0 / float(RTDE_FREQ))
    FREQ = 20
   
    USE_QUEUE = True
    STOP_SERVER = False

    def __init__(self, opcua_conn, opcuasettings, host = "192.168.0.108", port = PORT, freq = 20):
        self.HOST = host
        self.PORT = port
        self.FREQ = freq
        self.socket = None
        self.dqueue = deque(maxlen=3) # if time is critical, use queues with FIFO fashion in seperate threads 

        self.REFRESH_RATES = self.RTDE_FREQ / freq
        self.listeners =[]
        
        self.opcua_conn = opcua_conn
        self.opcuasettings = opcuasettings

    async def connect(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.settimeout(5)

        self.socket.connect((self.HOST, self.PORT))
       
        if not self.USE_QUEUE:
            recv_buff = self.socket.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)
            #print(f'rbuff: {recv_buff}')
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1024*2)

    async def idle(self):
        await asyncio.sleep(self.IDLE_TIME) 

    def subscribe(self, listener):
        pub.subscribe(listener, self.HOST)
        self.listeners.append(listener)

    async def process(self): # if use queue mechanism
        # data = self.dqueue.get(False, self.IDLE_TIME)
        if self.USE_QUEUE:
            try:
                data = self.dqueue.pop()
                # pub.sendMessage(self.HOST, data=data)
                await self.publish(data)
            except Exception as e: # empty queue
                pass
        
    async def publish(self, data):
        for listener in self.listeners:
            await listener(data)
            
    async def listen(self):
        self.socket.settimeout(2)

        cnt = 0

        head = self.socket.recv(4)
        mesgSize =  int.from_bytes(head, "big") # read the packet size only once
        data = self.socket.recv(mesgSize - 4)
        
        while self.STOP_SERVER is False:
            try:
                if True:
                    data = self.socket.recv(mesgSize)
                    data = data[4:] # remove header
                    
                    if self.USE_QUEUE:
                        if cnt % int(self.REFRESH_RATES) == 0:
                            self.dqueue.append(data)
                    else:
                        #pub.sendMessage(self.HOST, data=data) # not accept async
                        await self.publish(data)

                #await self.idle()
                cnt += 1
            except Exception as e:
                logging.error('socket receiving exception')
                self.connect()


    async def run_vrc_process(self):
        if self.USE_QUEUE:
            await self.opcua_conn.connect()
        
        while self.STOP_SERVER is False:
            await self.process()
            await self.idle()

    async def run_vrc_connector(self):
        if not self.USE_QUEUE:
            await self.opcua_conn.connect()
        
        self.STOP_SERVER = False
        await self.connect()
        await self.listen()

    def run_vrc_server_thread(vrc_conn):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(vrc_conn.run_vrc_connector())
        loop.run_forever()
        # loop.run_until_complete(vrc_conn.run_vrc_connector())


    def run_vrc_client_thread(vrc_conn):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(vrc_conn.run_vrc_process())
        loop.run_forever()
        # loop.run_until_complete(vrc_conn.run_vrc_process())

    
    def start_server(self):
        ur_vrc_th = threading.Thread(target=VRCConnector.run_vrc_server_thread, args=(self,))
        ur_vrc_client_th = threading.Thread(target=VRCConnector.run_vrc_client_thread, args=(self,))
        ur_vrc_th.start()
        ur_vrc_client_th.start()

    def stop_server(self):
        self.STOP_SERVER = True


    def upload_program(self):
        pass

if __name__ == '__main__':
    vrc_conn = VRCConnector()

    VRCConnector.run_vrc_server_thread(vrc_conn)