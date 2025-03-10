import logging
# import socket
from collections import deque
import asyncio
from pubsub import pub
import threading
from vrc_connector import VRCConnector
from conn_opcua.conn_opcua_client import OpcuaClientConn, BaseClientSubHandler

import struct
import logging
from asyncua import Client, Node, ua

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

class RexrothClientSubHandler(BaseClientSubHandler):
   
    def __init__(self):
        self.future = asyncio.Future()
        self.USE_QUEUE = False
        self.dqueue = deque(maxlen=3) # if time is critical, use queues with FIFO fashion in seperate threads 
        
    def pop(self):
        data = self.dqueue.pop()
        axes = struct.unpack('12d', data)
    
        return axes

    def add(self, axesActData):
        self.dqueue.append(axesActData)


    async def datachange_notification(self, node: Node, val, data):
        _logger.info('      datachange_notification %r %s', node, val)
        print('{}, {}'.format(node.nodeid, val))

class RexrothOpcuaClientConn(OpcuaClientConn):
    
    def __init__(self, host, port, freq=20):
        self.subhandler = RexrothClientSubHandler()
        self.freq = freq
        self.host = host
        self.port = port


class RexrothConnector(VRCConnector):
    def __init__(self, opcua_conn, opcuasettings, host = "127.0.0.1", port = 4840, freq = 20):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)


    async def relayAxes(self, axesVal):
        idx_arr = [
                'ns=4;s=FSCONNECTOR.X1',
                'ns=4;s=FSCONNECTOR.Y1',
                'ns=4;s=FSCONNECTOR.Z1',
                'ns=4;s=FSCONNECTOR.A1',
                'ns=4;s=FSCONNECTOR.C1',
                'ns=4;s=FSCONNECTOR.X2',
                'ns=4;s=FSCONNECTOR.Y2',
                'ns=4;s=FSCONNECTOR.Z2',
                'ns=4;s=FSCONNECTOR.A2',
                'ns=4;s=FSCONNECTOR.C2'
            ]
            
        await self.opcua_conn.writeArrayValues(idx_arr, axesVal)
        

    async def connect(self):
        self.rex_conn = RexrothOpcuaClientConn(host=self.HOST, port=self.PORT)
        await self.rex_conn.connect()

        self.subscribe(self.relayAxes)

    async def listen(self):
        cnt = 0
        while self.STOP_SERVER is False:
            try:
                if True:
                    axesAcChan1 = await self.rex_conn.readValue('ns=27;s=NC.Chan.AxisPosAcs,01,1')
                    axesAcChan2 = await self.rex_conn.readValue('ns=27;s=NC.Chan.AxisPosAcs,02,1')
                    axesAct = [
                        axesAcChan1[0],
                        axesAcChan1[1],
                        axesAcChan1[2],
                        axesAcChan1[3],
                        axesAcChan1[4],
                        axesAcChan2[0],
                        axesAcChan2[1],
                        axesAcChan2[2],
                        axesAcChan2[3],
                        axesAcChan2[4]
                    ]
                    self.rex_conn.subhandler.add(axesAct)

                    if self.FREQ != 0:
                        await asyncio.sleep(1.0/self.FREQ)
                    
                    # if self.USE_QUEUE:
                    #     if cnt % int(self.REFRESH_RATES) == 0:
                    #         self.dqueue.append(axesAct)
                    # else:
                    #await self.publish(axesAct)
                    await self.relayAxes(axesAct)

                #await self.idle()
                cnt += 1
            except Exception as e:
                logging.error('socket receiving exception')
