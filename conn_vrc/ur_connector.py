import logging
import socket
from collections import deque
import asyncio
import tkinter as tk
from tkinter import filedialog
from pubsub import pub
import threading
from conn_vrc.vrc_connector import VRCConnector
from conn_vrc.ur_uploader_util import URUtil

class URConnector(VRCConnector):
    
    def __init__(self, opcua_conn, opcuasettings, host = "192.168.1.59", port = 30003, freq = 60):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)

    async def listen(self):
        self.socket.settimeout(3)

        cnt = 0

        head = self.socket.recv(4)
        mesgSize =  int.from_bytes(head, "big") # read the packet size only once
        data = self.socket.recv(mesgSize - 4)

        while self.STOP_SERVER is False:
            try:
                # head = self.socket.recv(4)
                # mesgSize =  int.from_bytes(head, "big")
                # if mesgSize > 0:
                #     data = self.socket.recv(mesgSize - 4)
                if True:
                    data = self.socket.recv(mesgSize)
                    data = data[4:]


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
                await self.connect()

    def upload_program(self, content):
        # scriptFile = filedialog.askopenfilename()
        # if scriptFile != '':
        # URUtil(self.HOST).runScript(scriptFile)
        URUtil(self.HOST).runScriptWithContent(content)

if __name__ == '__main__':
    ur_conn = URConnector()
    URConnector.run_vrc_server_thread(ur_conn)