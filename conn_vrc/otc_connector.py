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
from asyncua import Node

logging.basicConfig(level=logging.WARNING)
_logger = logging.getLogger('asyncua')

class OtcClientSubHandler(BaseClientSubHandler):
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
        # print('{}, {}'.format(node.nodeid, val))



class OtcOpcuaClientConn(OpcuaClientConn):
    
    def __init__(self, host, port, freq=30):
        self.subhandler = OtcClientSubHandler()
        self.freq = freq
        self.host = host
        self.port = port


class OtcConnector(VRCConnector):
    def __init__(self, opcua_conn, opcuasettings, host = "192.168.1.2", port = 16664, freq = 20):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)
        self.future = asyncio.Future()
        
    async def relayAxes(self, axes):
        try:
            idx_arr = [
                f'{self.opcuasettings["Namespace"]}.D1',
                f'{self.opcuasettings["Namespace"]}.D2',
                f'{self.opcuasettings["Namespace"]}.D3',
                f'{self.opcuasettings["Namespace"]}.D4',
                f'{self.opcuasettings["Namespace"]}.D5',
                f'{self.opcuasettings["Namespace"]}.D6',
                f'{self.opcuasettings["Namespace"]}.J1',
                f'{self.opcuasettings["Namespace"]}.J2',
            ]
            
            values = [
                axes[40],
                axes[41],
                axes[42],
                axes[43],
                axes[44],
                axes[45],
                axes[0],
                axes[1],
            ]
            
            await self.opcua_conn.writeArrayValues(idx_arr, values)
            
        except Exception as e:
            logging.error(e)
            
            
    async def connect(self):
        self.otc_conn = OtcOpcuaClientConn(self.HOST, self.PORT)
        await self.otc_conn.connect() # connect to FSCONNECTOR opcua
        await self.opcua_conn.connect() # connect to OTC opcua

        # test
        #await self.otc_conn.addVariable('ns=4;s=FSCONNECTOR.Axes', 'Axes', [1.0,2.0,3.0,4.0,5.0,6.0])
        #self.subscribe(self.relayAxes)

    async def listen(self):
        cnt = 0
        while self.STOP_SERVER is False:
            try:
                if True:
                    # self.subhandler.A1 = await self.readValue('ns=8;s=5001.Robot.Axes.A1.ParameterSet.ActualPosition')
                    # self.subhandler.A2 = await self.readValue('ns=8;s=5001.Robot.Axes.A2.ParameterSet.ActualPosition')
                    # self.subhandler.A3 = await self.readValue('ns=8;s=5001.Robot.Axes.A3.ParameterSet.ActualPosition')
                    # self.subhandler.A4 = await self.readValue('ns=8;s=5001.Robot.Axes.A4.ParameterSet.ActualPosition')
                    # self.subhandler.A5 = await self.readValue('ns=8;s=5001.Robot.Axes.A5.ParameterSet.ActualPosition')
                    # self.subhandler.A6 = await self.readValue('ns=8;s=5001.Robot.Axes.A6.ParameterSet.ActualPosition')

                    axesAct = await self.otc_conn.readValue('ns=1;s=R1:R0[0..99]') # float array       
                    #self.otc_conn.subhandler.add(axesAct) # add to subhandler queue

                    if self.FREQ != 0:
                        await asyncio.sleep(1.0/self.FREQ)
                    
                    await self.relayAxes(axesAct)

                await self.idle()
                cnt += 1
            except Exception as e:
                logging.error('socket receiving exception')
