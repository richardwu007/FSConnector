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

class PLCCli(VrcCli):
        
    def __init__(self, portconf, opcua_conn, opcuasettings):
        self.opcua_conn = opcua_conn
        
        VrcCli.__init__(self,portconf, opcua_conn, opcuasettings)

    async def process(self, data):
        pass
