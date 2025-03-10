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

class SiasunWebCli(VrcCli):
        
    PAYLOAD_DICT = {
        'q actual': '7f', 'qd actual': '7f', 'qdd actual': '7f', 'M actual': '7f', 
        'q target': '7f', 'qd target': '7f', 'qdd target': '7f', 'M target': '7f',            
        'Motor temperatures': '7f',  'I actual': '7f', 'q control error': '7I', 'q control state': '7I',
        'reserved 1': '32B', 'Tool vector actual': '6f', 'Tool vector actual': '6f', 'TCP speed actual': '6f', 
        'TCP acceleration actual': '6f', 'TCP force actual': '6f', 'Tool vector target': '6f', 'TCP speed target': '6f', 
        'TCP acceleration target': '6f', 'TCP force target': '6f', 'Base force actual': '6f', 'Base force target': '6f', 
        'TCP values': '6f', 'Baseframe values': '6f','reserved 2': '64B', 'Function input bits': '8B', 
        'Function output bits': '8B', 'Digital input bits': '16B', 'Digital output bits': '16B', 'Analog inputs': '8f', 
        'Analog outputs': '8f', 'Float register inputs': '32f', 'Float register outputs': '32f', 'Function bool register inputs': '16B', 
        'Function bool register outputs': '16B', 'Bool register inputs': '64B', 'Bool register outputs': '64B', 'Word register inputs': '32h',
        'Word register outputs': '32h', 'reserved 3': '32B', 'TCP DI': '8B', 'TCP DO': '8B',
        'TCP AI': '2f', 'TCP AO': '2f', 'TCP button state': '2B', 'reserved 4': '6B',
        'Robot mode': '1b', 'Robot state': '1b', 'Robot program state': '1b', 'Safety state': '1b', 
        'Collision signal': '1b', 'Collided joint': '1b', 'reserved 5': '2B', 'Robot error code': '1I',  
        'reserved 6': '8B'}
    
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
        value = struct.unpack(fmt, query_data)

        return value

    def _processQactual(self, data):
        value = self._unpack_data(data, "q actual")
        # convert raidans to degrees
        value = map(lambda v: v * (180.0/math.pi), value)
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
        data = self._unpack_data(data, "Digital output bits")
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
            inputs = self._processInputs(data)
            outputs = self._processOutputs(data)

            await self.publishToOpcua(joints, inputs, outputs)
        except Exception as e:
            return None       
