import logging
import random
import socket
import struct
import math
import time
# from time import sleep, time
# import numpy as np
import json
from collections import deque
import asyncio
import sys

from conn_opcua.conn_opcua_client import OpcuaClientConn

sys.path.append('./conn_vrc')
from ur_connector import URConnector
from vrc_cli import VrcCli

class DualMachineCli(VrcCli):
    
    def __init__(self, portconf, opcua_conn, opcuasettings):
        self.opcua_conn = opcua_conn

        VrcCli.__init__(self,portconf, opcua_conn, opcuasettings)
        
        # asyncio.run(self.opcua_conn.connect())
                

    def _processQactual(self, data):
        joint_regs = data[2]
        
        return joint_regs        
        # test unpack joint registers
        #X1 = struct.unpack('!d', joint_regs[0:8])[0]
        
        X1 = random.uniform(0, 1) * 4000.0
        Y1 = random.uniform(0, 1) * 1400.0
        Z1 = random.uniform(0, 1) * 800.0
        A1 = 0.0
        C1 = 0.0
        X2 = random.uniform(0, 1) * 4000.0
        Y2 = random.uniform(0, 1) * 1400.0
        Z2 = random.uniform(0, 1) * 800.0
        A2 = 0.0
        C2 = 0.0
        
        return [X1, Y1, Z1, A1, C1, X2, Y2, Z2, A2, C2]
    
    def _processInputs(self, data):
        return data[0]

    def _processOutputs(self, data):
        return data[1]

    async def process(self, data):
        try:
            # data = self.dqueue.get(False, self.IDLE_TIME)
            # data = self.dqueue.pop()
            #self._processAll(data)

            joints = self._processQactual(data)
            inputs = self._processInputs(data)
            outputs = self._processOutputs(data)

            await self.publishToOpcua(joints, inputs, outputs)
        except Exception as e:
            return None       
