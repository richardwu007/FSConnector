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
from vrc_cli import VrcCli

class KeberConveyorCli(VrcCli):
        
    def __init__(self, portconf, opcua_conn, opcuasettings):
        self.opcua_conn = opcua_conn
        
        VrcCli.__init__(self,portconf, opcua_conn, opcuasettings)


    async def publishToOpcua(self, joints, inputs, outputs):
        if self.opcua_conn is None: return
        idx_arr = []
        values = []
        
        if joints is not None:
            for joint in joints:
                idx = "{}.{}".format(self.opcua_ns, joint[0])
                
                idx_arr.append(idx)
                values.append(joint[1])
                
            try:
                await self.opcua_conn.writeArrayValues(idx_arr, values)
            except Exception as e:
                pass
    
        idx_arr = []
        values = []
        if outputs is not None:
            for out in outputs:
                idx = "{}.{}".format(self.opcua_ns, out[0])
                
                idx_arr.append(idx)
                values.append(out[1])
                
            try:
                await self.opcua_conn.writeArrayValues(idx_arr, values)
            except Exception as e:
                pass



    async def process(self, motions):
        try:

            joints = motions[0]
            inputs = motions[1]
            outputs = motions[2]

            await self.publishToOpcua(joints, inputs, outputs)
        except Exception as e:
            return None       
