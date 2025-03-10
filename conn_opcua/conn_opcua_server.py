import logging
import asyncio
import sys, os, pathlib
sys.path.insert(0, "..")

from asyncua import ua, Server
from asyncua.common.methods import uamethod

import threading
logging.basicConfig(level=logging.WARNING)
class OpcuaServerConn:
    _instance = None

    server = None
    myObj = None
    opcua_server_th = None
    STOP_SERVER = False

    def __new__(cls, *args, **kw):
        if cls._instance is None:
            cls._instance = object.__new__(cls, *args, **kw)
        return cls._instance

    @uamethod
    def func(self, parent, value):
        return value * 2
    
        
    async def addVariable(self, var_idx, var_name, var_val, varianttype=None):
        myvar = await self.myObj.add_variable(var_idx, var_name, var_val, varianttype)
        await myvar.set_writable()

    async def runOpcServer(self, opcua_namespace, host, port, serverupCallback=None):
        _logger = logging.getLogger('asyncua')
        # setup our server

        self.server = Server()
        await self.server.init()
        self.server.set_endpoint("opc.tcp://{}:{}".format(host, str(port)))

        self.server.set_security_policy([
            ua.SecurityPolicyType.NoSecurity,
            # ua.SecurityPolicyType.Basic256_SignAndEncrypt,
            # ua.SecurityPolicyType.Basic256_Sign,
        ])

        # setup our own namespace, not really necessary but should as spec
        uri = 'http://examples.freeopcua.github.io'
        idx = await self.server.register_namespace(uri)
        _logger.info("idx is: %r", idx)



        # populating our address space
        # server.nodes, contains links to very common nodes like objects and root
        self.myObj = await self.server.nodes.objects.add_object(opcua_namespace, 'MyObject')

        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A1.ParameterSet.ActualPosition", 'D1', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A2.ParameterSet.ActualPosition", 'D2', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A3.ParameterSet.ActualPosition", 'D3', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A4.ParameterSet.ActualPosition", 'D4', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A5.ParameterSet.ActualPosition", 'D5', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A6.ParameterSet.ActualPosition", 'D6', 0.0)
        # await myvar.set_writable()
        KUKA_MODE = False
        if KUKA_MODE == True:
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.D1", 'D1', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.D2", 'D2', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.D3", 'D3', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.D4", 'D4', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.D5", 'D5', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.D6", 'D6', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.E1", 'E1', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.E2", 'E2', 0.0)
            await myvar.set_writable()
            myvar = await self.myObj.add_variable("ns=4;s=UR_CELL.E3", 'E3', 0.0)
            await myvar.set_writable()
        
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A1.ParameterSet.ActualPosition", 'D1', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A2.ParameterSet.ActualPosition", 'D2', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A3.ParameterSet.ActualPosition", 'D3', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A4.ParameterSet.ActualPosition", 'D4', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A5.ParameterSet.ActualPosition", 'D5', 0.0)
        # await myvar.set_writable()
        # myvar = await self.myObj.add_variable("ns=8;s=5001.Robot.Axes.A6.ParameterSet.ActualPosition", 'D6', 0.0)
        # await myvar.set_writable()
        
        # nodefile = os.path.join(str(pathlib.Path(__file__).parent.resolve()), "custom_nodes.xml")
        # await server.import_xml(nodefile)

        # Set MyVariable to be writable by clients
        

        # await server.nodes.objects.add_method(ua.NodeId('ServerMethod', 2), ua.QualifiedName('ServerMethod', 2), self.func, 
        #                                       [ua.VariantType.Int64], [ua.VariantType.Int64])
        _logger.info('Starting server!')
        await self.server.start()

        if serverupCallback is not None: serverupCallback()

        self.STOP_SERVER = False
        # async with self.server: 
        while self.STOP_SERVER is False:
            await asyncio.sleep(0.1)
        
        await self.server.stop()

    def stop_server(self):
        self.STOP_SERVER = True

    async def run_opcua_server(server, opcua_namespace, host, port, callback):
        await server.runOpcServer(opcua_namespace, host=host, port=port, serverupCallback=callback) 

    def run_opcua_server_thread(server, opcua_namespace, host, port, callback):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(OpcuaServerConn.run_opcua_server(server, opcua_namespace, host, port, callback))
        loop.run_forever()


    def start_server(self, opcua_namespace, host, port, serverupCallback):
        self.opcua_server_th = threading.Thread(target=OpcuaServerConn.run_opcua_server_thread, args=(self, opcua_namespace, host, port, serverupCallback))
        self.opcua_server_th.start()
        

    # def stop_server(self):
        # loop = asyncio.get_event_loop()
        # loop.create_task(self.stopServer())
        # loop.run_until_complete(self.stopServer())


if __name__ == '__main__':

    logging.basicConfig(level=logging.DEBUG)
    server = OpcuaServerConn()
    asyncio.run(server.runOpcServer(), debug=True) 
