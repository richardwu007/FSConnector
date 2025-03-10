import asyncio
import sys
from pathlib import Path

from conn_web.conn_websocket import WebSocketConn
sys.path.insert(0, str(Path(__file__).parent.parent))
import logging
from asyncua import Client, Node, ua
from conn_opcua.conn_opcua_server import OpcuaServerConn

import threading
import struct 
    
logging.basicConfig(level=logging.ERROR)
_logger = logging.getLogger('asyncua')
_logger.setLevel(logging.ERROR)

class BaseClientSubHandler:
    """
    More advanced subscription client using Future, so we can wait for events in tests
    """
    myValue = 0
    
    def __init__(self):
        self.future = asyncio.Future()

    def reset(self):
        self.future = asyncio.Future()

    # def datachange_notification(self, node, val, data):
    #     self.future.set_result((node, val, data))

    def event_notification(self, event):
        self.future.set_result(event)

    def datachange_notification(self, node: Node, val, data):
        """
        Callback for asyncua Subscription.
        This method will be called when the Client received a data change message from the Server.
        """
        _logger.info('      datachange_notification %r %s', node, val)

        self.myValue = val
    
    def getValue(self):
        return self.myValue

class OpcuaClientConn:
    _instance = None
    regNodes = []
    URL = ""
    opcua_client_th = None
    websocket = None
    STOP_SERVER = False
    port = 4842
    host = "127.0.0.1"

    counter = 0
    # def __new__(cls, *args, **kw):
    #     if cls._instance is None:
    #         cls._instance = object.__new__(cls, *args, **kw)
    #     return cls._instance
    def __init__(self, host, port, subhandler = BaseClientSubHandler()):
        self.subhandler = subhandler
        self.host = host
        self.port = port
        
    async def addVariable(self, var_idx, var_name, var_val, val_type=None):
        if self.client.get_node(var_idx) is not None:
            server = OpcuaServerConn()
            await server.addVariable(var_idx, var_name, var_val, val_type)

    def registerNode(self, var_idx, var_name, var_val, val_type=None):
        self.regNodes.append((var_idx, var_name, var_val, val_type))

    async def addVariablesFromRegNodes(self):
        for node in self.regNodes:
            try:
                await self.addVariable(node[0], node[1], node[2], node[3])
            except Exception as e:
                print(e)
            
    async def readValue(self, idx):
        var = self.client.get_node(idx)

        return await var.read_value()

    async def writeValue(self, idx, value, ns=None, ):
        # uri = 'http://examples.freeopcua.github.io'
        # idx = await self.client.get_namespace_index(uri)
            # idx = await client.get_namespace_index(uri="http://examples.freeopcua.github.io")
            
            # get a specific node knowing its node id 
            
            # var = client.get_node(ua.NodeId(1002, 2))
            # var = client.get_node("ns=3;i=2002")
        # var = await self.client.nodes.root.get_child(["0:Objects", f"{idx}:MyObject", f"{idx}:JOINT1"])
        var = self.client.get_node(idx)
        #val = await var.get_data_value()
        try:
            await var.write_value(value)
        except Exception as e:
            print(e) # reconnect
            await self.connect()

    async def writeArrayValues(self, idx_arr, values, ns=None):
        nodes = [self.client.get_node(idx) for idx in idx_arr]
        await self.client.write_values(nodes, values)
        
    async def waitUntilConnected(self):
        while not self.HAS_CONNECTED:
            await asyncio.sleep(1)  


    async def postConnected(self):
        # self.counter += 2
        # # try:
        # val = await self.readValue('ns=4;s=UR_CELL.D1')
        # #     await self.writeValue('ns=4;s=UR_CELL.D1', float(self.counter % 360))
        # # except Exception as e:
        # #     pass
        # var = self.client.get_node('ns=4;s=UR_CELL.D1')
        # #val = await var.get_data_value()
        # await var.write_value(float(self.counter))
        
        await asyncio.sleep(1)
    
    async def connect(self, nodes=[]):
        self.URL = "opc.tcp://{}:{}".format(self.host, str(self.port))
        
        # url = 'opc.tcp://commsvr.com:51234/UA/CAS_UA_Server'
        async with Client(url=self.URL) as client:
            self.client = client
            # Client has a few methods to get proxy to UA nodes that should always be in address space such as Root or Objects
            # Node objects have methods to read and write node attributes as well as browse or populate address space
            #_logger.info('Children of root are: %r', await client.nodes.root.get_children())

            # uri = 'http://examples.freeopcua.github.io'
            # idx = await client.get_namespace_index(uri)
            # idx = await client.get_namespace_index(uri="http://examples.freeopcua.github.io")
            
            # get a specific node knowing its node id 
            #idxObj = "ns=4;s=UR_CELL"
            # idxJoint = "ns=4;s=UR_CELL.D1"
            # var = client.get_node(ua.NodeId(1002, 2))
            # var = client.get_node(idxJoint)
            # var = await client.nodes.root.get_child(["0:Objects", f"{idxObj}:MyObject", f"{idxJoint}:JOINT1"])
            # print("My variable                     ", var, await var.read_value())
            # print(var)
            # await var.read_data_value() # get value of node as a DataValue object
            # await var.read_value() # get value of node as a python builtin
            # await var.write_value(ua.Variant([23], ua.VariantType.Int64)) #set node value using explicit data type
            # await var.write_value(3.9) # set node value using implicit data type
            # self.myValue = await var.read_value()
            
            # We create a Client Subscription.
            subscription = await client.create_subscription(10, self.subhandler)
            # nodes = [
            #     client.get_node("ns=4;s=UR_CELL.D1"),
            #     client.get_node("ns=4;s=UR_CELL.D2"),
            #     client.get_node("ns=4;s=UR_CELL.D3"),
            #     client.get_node("ns=4;s=UR_CELL.D4"),
            #     client.get_node("ns=4;s=UR_CELL.D5"),
            #     client.get_node("ns=4;s=UR_CELL.D6")
            #     #client.get_node(ua.ObjectIds.Server_ServerStatus_CurrentTime),
            # ]
            
            # # We subscribe to data changes for two nodes (variables).
            if any(nodes):
                await subscription.subscribe_data_change(map(lambda n: client.get_node(n), nodes))
            # We let the subscription run for ten seconds
            # await asyncio.sleep(1)
            # We delete the subscription (this un-subscribes from the data changes of the two variables).
            # This is optional since closing the connection will also delete all subscriptions.
            #await subscription.delete()
            # After one second we exit the Client context manager - this will close the connection.
            #await asyncio.sleep(1)
            
            await self.addVariablesFromRegNodes()

            # while(self.STOP_SERVER == False): # Keep connection alive or modify __aexit__ function to discard disconnection in asuncua/client.py                         
            #     await self.postConnected()

    async def disconnect(self):
        await self.client.disconnect() 
    
    async def run_test(self):
        a = await self.readValue('ns=4;s=UR_CELL.TEST')
        print(a)
        await self.writeValue('ns=4;s=UR_CELL.TEST', -100.0)
        print(a)


    async def run_opcua_client(self, nodes):
        self.STOP_SERVER = False
        await self.connect(nodes=nodes)
        
        # while self.STOP_SERVER is False:
        #     await self.postConnected()

    def run_opcua_client_thread(client, nodes):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        loop.create_task(client.run_opcua_client(nodes))
        
        # if client.websocket is not None:
        #     loop.create_task(client.websocket.run())
        #     client.websocket.run()
        
        loop.run_forever()

    def start_server(self, nodes=[]):
        #self.websocket = WebSocketConn(self)
        self.opcua_client_th = threading.Thread(target=OpcuaClientConn.run_opcua_client_thread, args=(self, nodes))
        self.opcua_client_th.start()

if __name__ == '__main__':
    
    
    import sys, os, inspect
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))))
    from settings import Settings
    Settings.set('settings.conf')
    settings = Settings.read()
    opcuasettings = settings['OPCUAServer']
    
    opcua_server = OpcuaServerConn()
    opcua_server.start_server(opcua_namespace=opcuasettings['Namespace'], host=opcuasettings['HOST'], port=opcuasettings['PORT'], serverupCallback=runTest)
    