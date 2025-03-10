import logging
import socket
import struct
import math
import time
# from time import sleep, time
# import numpy as np
import json
from collections import deque

import sys

from conn_opcua.conn_opcua_client import OpcuaClientConn

sys.path.append('./conn_vrc')
from ur_connector import URConnector
from vrc_cli import VrcCli

class StepProxyWebCli(VrcCli):
        
    PAYLOAD_DICT = {
        'q actual': '6f',  'Digital output byte': '1b'}
    
    PAYLOAD_LOOKUP = PAYLOAD_DICT.copy()

    def __init__(self, portconf, opcua_conn, opcuasettings):
        idx = 0
        length=range(len(self.PAYLOAD_DICT))      # Initialize pack indices
        for key,i in zip(self.PAYLOAD_DICT, length):
            fmtsize = struct.calcsize(self.PAYLOAD_DICT[key])

            self.PAYLOAD_LOOKUP[key] = idx, idx + fmtsize
            idx = idx + fmtsize

        VrcCli.__init__(self,portconf, opcua_conn, opcuasettings)

        # asyncio.run(self.opcua_conn.connect())
        
    
    def _unpack_data(self, data, key):
        
        idxes = self.PAYLOAD_LOOKUP[key] # start, end
        query_data = data[idxes[0]:idxes[1]]
        
        fmt = "<" + self.PAYLOAD_DICT[key] # little endian
        #fmt = ">" + self.PAYLOAD_DICT[key] # big endian
        
        value = struct.unpack(fmt, query_data)

        return value

    def _processQactual(self, data):
        value = self._unpack_data(data, "q actual")
        return list(value)
    
    def _processInputs(self, data):
        value = self._unpack_data(data, "Digital input bits")
        value = 0
        # an array of 16 bits in a list, convert 16bits to an integer
        i = 0
        for d in data:
            value += d << i
            i += 1
        return value

    def _processOutputs(self, data):
        data = self._unpack_data(data, "Digital output byte")
        value = 0
        # an array of 16 bits in a list, convert 16bits to an integer
        i = 0
        for d in data:
            value += d << i
            i += 1
            
        return value

    def _processAll(self, data):
        for key in self.PAYLOAD_DICT:
            value = self._unpack_data(data, key)
            print("{}: {}".format(key, str(value)))

    async def process(self, data):
        try:
            # data = self.dqueue.get(False, self.IDLE_TIME)
            # data = self.dqueue.pop()
            #self._processAll(data)

            joints = self._processQactual(data)
            inputs = None #self._processInputs(data)
            outputs = self._processOutputs(data)

            await self.publishToOpcua(joints, inputs, outputs)
        except Exception as e:
            return None       
