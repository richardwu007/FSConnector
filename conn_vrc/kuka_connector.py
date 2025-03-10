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

class KukaClientSubHandler(BaseClientSubHandler): 
    def __init__(self):
        self.future = asyncio.Future()
        
        self.A1 = 0.0
        self.A2 = 0.0
        self.A3 = 0.0
        self.A4 = 0.0
        self.A5 = 0.0
        self.A6 = 0.0
        
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

        # await self.conn.writeValue("ns={};s={}".format(node.nodeid.NamespaceIndex ,node.nodeid.Identifier), val)
        if 'Axes.A1' in str(node.nodeid):
            # await self.conn.writeValue("ns=4;s=UR_CELL.D1", val)
            # loop.run_until_complete(asyncio.wait(self.conn.writeValue("ns=4;s=UR_CELL.D1", val)))
            self.A1 = val
        elif 'Axes.A2' in str(node.nodeid):
            self.A2 = val
        elif 'Axes.A3' in str(node.nodeid):
            self.A3 = val
        elif 'Axes.A4' in str(node.nodeid):
            self.A4 = val
        elif 'Axes.A5' in str(node.nodeid):
            self.A5 = val
        elif 'Axes.A6' in str(node.nodeid):
            self.A6 = val


class KukaOpcuaClientConn(OpcuaClientConn):
    
    def __init__(self, host, port, freq=20):
        self.subhandler = KukaClientSubHandler()
        self.freq = freq
        self.host = host
        self.port = port


class KukaConnector(VRCConnector):
    def __init__(self, opcua_conn, opcuasettings, host = "192.168.239.128", port = 4840, freq = 20):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)


    async def relayAxes(self, axes):
        
        idx_arr = [
                f'{self.opcuasettings["Namespace"]}.D1',
                f'{self.opcuasettings["Namespace"]}.D2',
                f'{self.opcuasettings["Namespace"]}.D3',
                f'{self.opcuasettings["Namespace"]}.D4',
                f'{self.opcuasettings["Namespace"]}.D5',
                f'{self.opcuasettings["Namespace"]}.D6',
            ]
            
        values = [
            axes[0],
            axes[1],
            axes[2],
            axes[3],
            axes[4],
            axes[5]
        ]
            
        await self.opcua_conn.writeArrayValues(idx_arr, values)
        

    async def connect(self):
        self.kuka_conn = KukaOpcuaClientConn(host=self.HOST, port=self.PORT)
        await self.kuka_conn.connect()

        self.subscribe(self.relayAxes)

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
                    axesAct = await self.kuka_conn.readValue('ns=8;s=ns=7%3Bi=5004??krlvar:/System/R1#$AXIS_ACT')        
                    # self.opcua_conn.subhandler.add(axesAct.Body)

                    if self.FREQ != 0:
                        await asyncio.sleep(1.0/self.FREQ)
                    
                    await self.publish(axesAct.Body)

                #await self.idle()
                cnt += 1
            except Exception as e:
                logging.error('socket receiving exception')
