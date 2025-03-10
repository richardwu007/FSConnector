import asyncio
import sys
# sys.path.insert(0, "..")
import logging

import websockets
import json
import ast

# from conn_opcua.conn_opcua_client import OpcuaClientConn

logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('websocket')

import threading

conn = None
async def handler(websocket, path):
        
    # data = await websocket.recv()
    #asyncio.run(conn.connect())
    
    async for data in websocket:
        d=json.loads(data)

        cmd = d['cmd']
        idx = d['idx']
        varname = d['name']

        try:        
            if cmd == 'add':
                val = ast.literal_eval(str(d['val']))
                await conn.addVariable(idx, varname, val)
                reply = {"varname": varname, "val": val}
                await websocket.send(json.dumps(reply))
            elif cmd == 'wait':
                await asyncio.sleep(val)
            elif cmd == 'write':
                val = ast.literal_eval(str(d['val']))
                await conn.writeValue(idx, val)
                reply = {"varname": varname, "val": val}
                await websocket.send(json.dumps(reply)) # '{"varname": "Rz", "val": 488}'
            elif cmd == 'read':
                res = await conn.readValue(idx)
                await websocket.send(json.dumps( {"varname": varname, "val": res}))
            elif cmd == 'batch_read':
                allres = []
                for name in varname:
                    res = await conn.readValue(idx + '.' + name)
                    allres.append({"varname": name, "val": res})
                await websocket.send(json.dumps(allres))
            elif cmd == 'initialized':
                HAS_INITED = True
        except Exception as e:
            print(e)
            pass

class WebSocketConn:
    def __init__(self, websocketsettings, opc_conn = None):
        self.future = asyncio.Future()
        self.opc_conn = opc_conn
        self.websocketsettings = websocketsettings
    
    async def run(self):
        # start_server = websockets.serve(self.handler, "0.0.0.0", 8000)
        # await start_server
        global conn
        conn = self.opc_conn # TBD: not multithread safe
        try:
            if conn is not None:
                await conn.connect()
            server = await websockets.serve(handler, self.websocketsettings["HOST"], self.websocketsettings["PORT"], ping_interval=None) # fix: sent 1011 (unexpected error) keepalive ping timeout; no close frame received
            # await server.wait_closed()
        except Exception as e:
            print(e)
            pass
    
    
    def run_websocket_server_thread(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.create_task(self.run())
        loop.run_forever()
    
    def start_server(self):
        self.websocket_th = threading.Thread(target=WebSocketConn.run_websocket_server_thread, args=(self,))
        self.websocket_th.start()

        # loop.run_until_complete(self.run())
    
    def stop(self):
        pass

if __name__ == '__main__':
    import os, inspect
    sys.path.append(str(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe()))))))
    from settings import Settings
    websocketsettings = Settings.readWebSocketServerConfig()
    conn = WebSocketConn(websocketsettings)
    
    conn.start_server()

