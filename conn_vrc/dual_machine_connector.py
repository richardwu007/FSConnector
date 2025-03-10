import logging
import socket
from collections import deque
import asyncio
from tkinter import filedialog
from pubsub import pub
import threading
from conn_vrc.vrc_connector import VRCConnector
from conn_vrc.ur_uploader_util import URUtil
from pyModbusTCP.client import ModbusClient
from conn_opcua.conn_opcua_client import OpcuaClientConn, BaseClientSubHandler
import struct

_logger = logging.getLogger('asyncua')

class DualMachineConnector(VRCConnector):
    
    def __init__(self, opcua_conn, opcuasettings, host = "127.0.0.1", port = 30003, freq = 60):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)

        self.lastGranted = 1

        
    # can only one asker gain the critical section, prefer the last one
    def gainCriticalSection(self, asker):
        if self.lastGranted == asker:
            self.lastGranted = asker
            return True
        else:
            return False

    async def connect(self):
        self.socket = ModbusClient(host=self.HOST, port=self.PORT, unit_id=1, auto_open=True)
        await self.opcua_conn.connect()


    async def interlockABZones(self):
        req1 = await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.ReqZone1")
        grant1 = req1
        req2 = await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.ReqZone2")
        grant2 = req2
        
        if req1 and req2:
            grant1 = self.gainCriticalSection(1)
            grant2 = self.gainCriticalSection(2)
        
        
        runningA = await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.RunningA")
        runningB = await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.RunningB")
        
        inputs = req1 + (req2 << 1) + (runningA << 2) + (runningB << 3)
        outputs = grant1 + (grant2 << 1)
        
        return inputs, outputs

    async def listen(self):
        while self.STOP_SERVER is False:
            #regs = self.socket.read_holding_registers(0, 2)
            #if regs:
            #    data = regs[0]
                # print(data)
                
            # Adresses of Modbus registers
            JOINT_ADDR = 0 # 10168
            JOINT_LEN = 10
            
            if self.socket.open():
                joint_regs = self.socket.read_holding_registers(JOINT_ADDR, JOINT_LEN)
            
            try:
                inputs, outputs = await self.interlockABZones()
                
                await self.publish([inputs, outputs, joint_regs])
                    
                await self.idle()
            except Exception as e:
                logging.error('socket receiving exception')
                await self.connect()




if __name__ == '__main__':
    ur_conn = DualMachineConnector()
    DualMachineConnector.run_vrc_server_thread(ur_conn)