import logging
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

class URWebCli(VrcCli):
    # Ref: https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/rtde-guide.html

    # PAYLOAD_DICT = {'MessageSize': 'i', 'Time': 'd', 'q target': '6d', 'qd target': '6d', 'qdd target': '6d','I target': '6d',
    #     'M target': '6d', 'q actual': '6d', 'qd actual': '6d', 'I actual': '6d', 'I control': '6d',
    #     'Tool vector actual': '6d', 'TCP speed actual': '6d', 'TCP force': '6d', 'Tool vector target': '6d',
    #     'TCP speed target': '6d', 'Digital input bits': 'd', 'Motor temperatures': '6d', 'Controller Timer': 'd',
    #     'Test value': 'd', 'Robot Mode': 'd', 'Joint Modes': '6d', 'Safety Mode': 'd', 'empty1': '6d', 'Tool Accelerometer values': '3d',
    #     'empty2': '6d', 'Speed scaling': 'd', 'Linear momentum norm': 'd', 'SoftwareOnly': 'd', 'softwareOnly2': 'd', 'V main': 'd',
    #     'V robot': 'd', 'I robot': 'd', 'V actual': '6d', 'Digital outputs': 'd', 'Program state': 'd', 'Elbow position': '3d', 'Elbow velocity': '3d'}
    PAYLOAD_DICT = {'Time': 'd', 'q target': '6d', 'qd target': '6d', 'qdd target': '6d','I target': '6d',
        'M target': '6d', 'q actual': '6d', 'qd actual': '6d', 'I actual': '6d', 'I control': '6d',
        'Tool vector actual': '6d', 'TCP speed actual': '6d', 'TCP force': '6d', 'Tool vector target': '6d',
        'TCP speed target': '6d', 'Digital input bits': 'd', 'Motor temperatures': '6d', 'Controller Timer': 'd',
        'Test value': 'd', 'Robot Mode': 'd', 'Joint Modes': '6d', 'Safety Mode': 'd', 'empty1': '6d', 'Tool Accelerometer values': '3d',
        'empty2': '6d', 'Speed scaling': 'd', 'Linear momentum norm': 'd', 'SoftwareOnly': 'd', 'softwareOnly2': 'd', 'V main': 'd',
        'V robot': 'd', 'I robot': 'd', 'V actual': '6d', 'Digital outputs': 'd', 'Program state': 'd', 'Elbow position': '3d', 'Elbow velocity': '3d'}

    PAYLOAD_LOOKUP = PAYLOAD_DICT.copy()

    def __init__(self, portconf, opcua_conn, opcuasettings):
        self.opcua_conn = opcua_conn
        
        idx = 0
        length=range(len(self.PAYLOAD_DICT))      # Initialize pack indices
        for key,i in zip(self.PAYLOAD_DICT, length):
            fmtsize = struct.calcsize(self.PAYLOAD_DICT[key])

            self.PAYLOAD_LOOKUP[key] = idx, idx + fmtsize
            idx = idx + fmtsize

        VrcCli.__init__(self,portconf, opcua_conn, opcuasettings)
    
    def _unpack_data(self, data, key):
        
        idxes = self.PAYLOAD_LOOKUP[key] # start, end
        query_data = data[idxes[0]:idxes[1]]
        fmt = "!" + self.PAYLOAD_DICT[key]
        value = struct.unpack(fmt, query_data)

        return value

    def _processQactual(self, data):
        value = self._unpack_data(data, "q actual")
        value = map(lambda v: v * (180.0/math.pi), value)
        return list(value)
    
    def _processInputs(self, data):
        value = self._unpack_data(data, "Digital input bits")
        return value

    def _processOutputs(self, data):
        value = self._unpack_data(data, "Digital outputs")
        return value

    def _processAll(self, data):
        for key in self.PAYLOAD_DICT:
            value = self._unpack_data(data, key)
            print("{}: {}".format(key, str(value)))

    async def process(self, data):
        try:
            joints = self._processQactual(data)
            inputs = self._processInputs(data)
            outputs = self._processOutputs(data)

            await self.publishToOpcua(joints, inputs, outputs[0])
        except Exception as e:
            return None       
