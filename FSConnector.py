import logging
import argparse
import os
from conn_web.conn_websocket import WebSocketConn

from settings import Settings
from websockets.sync.client import connect
# from websockets import connect
import json
from conn_web.conn_webview import WebViewConn
from run_vrcservers import runOpcuaServer, runVRCServer, uploadProgram

class APIWebsocketConnect():
    def __init__(self, api_obj):
        self.api_obj = api_obj
    
    def __enter__(self):
        try:
            if self.api_obj.websocket is None:
                self.api_obj.websocket = connect(self.api_obj.websocketuri, close_timeout=None, open_timeout=None)
        except Exception as e:
            print(e)
            self.api_obj.websocket = None
        
        return self.api_obj.websocket

    def __exit__(self, *args):
        pass # retain websocket
    
class WebviewAPI:
    
    def __init__(self):
        # self.conn = conn
        # self.window = window
        self.websocket = None
        self.namespace = Settings.readOPCUAServerConfig()['Namespace']
        self.nameserver = f'{self.namespace}'
        self.nameserver += '.{}'
        self.websocketuri = f"ws://{Settings.readWebSocketServerConfig()['HOST']}:{Settings.readWebSocketServerConfig()['PORT']}/"
    
    def reconnect(self):
        self.websocket = connect(self.websocketuri, close_timeout=None, open_timeout=None, user_agent_header='Safari/537.36')
        # self.websocket = connect(self.websocketuri)
    # def connect_websocket(self):
    #     self.websocket = connect("ws://127.0.0.1:8000/")
    
    def send(self, data):
        try:
            self.websocket.send(data)
        except Exception as e:
            print(e)
            self.reconnect()
            self.websocket.send(data)
            
    # @api
    def item_selected(self, params):
        selected_item = params
        print(f"You selected: {selected_item}")
        return "Item selected successfully"
    
    def button_clicked(self, name, val):
        print(f"You clicked: {name}")
        
        with APIWebsocketConnect(self) as websocket:
            req = {'cmd': 'write', 'idx': self.nameserver.format(name), 'name': name, 'val': val}
            self.send(json.dumps(req))
            # message = websocket.recv() # too frequent reads-and-writes cause opcua server to crash
            # print(f"Received: {message}")
            
        return "Button clicked successfully"

    def refresh(self, name):
        with APIWebsocketConnect(self) as websocket:
            req = {'cmd': 'read', 'idx': self.nameserver.format(name), 'name': name}
            self.send(json.dumps(req))
            
            message = websocket.recv()
            return message
        
    def batch_refresh(self, names):
        with APIWebsocketConnect(self) as websocket:
            req = {'cmd': 'batch_read', 'idx': self.namespace, 'name': names}
            self.send(json.dumps(req))
            message = websocket.recv()
            
            return message
        
    def update_joint(self, name, val):
        with APIWebsocketConnect(self) as websocket:
        # if self.websocket is None:
        #     self.connect_websocket()    
            req = {'cmd': 'write', 'idx': self.nameserver.format(name), 'name': name, 'val': float(val)}
            self.send(json.dumps(req)) # '{"cmd": "write", "idx": "ns=4;s=PLC_CELL.Rz", "name": "Rz", "val": 3.0}'
            # message = websocket.recv()
            # print(f"Received: {message}")
            # return message
        
    def createPorts(self, portmaps):
        for jport in portmaps['Joints']:
            req = {'cmd': 'add', 'idx': self.nameserver.format(jport["Name"]), 'name': jport["Name"], 'val': float(jport["Val"])}
            self.send(json.dumps(req))
                
        for out in portmaps['OutputPorts']:
            req = {'cmd': 'add', 'idx': self.nameserver.format(out["Name"]), 'name': out["Name"], 'val': False}
            self.send(json.dumps(req))
        
        for inp in portmaps['InputPorts']:
            req = {'cmd': 'add', 'idx': self.nameserver.format(inp["Name"]), 'name': inp["Name"], 'val': False}
            self.send(json.dumps(req))

    def start(self, portconfjson:str):
        print("Starting Webview API")

        self.portconf = json.loads(portconfjson)
        runOpcuaServer(self.post_start)  

    def post_start(self):
        runVRCServer(self.portconf)
        
        self.post_load_settings()
        
    def post_load_settings(self, portmaps_config=None):
        global gWebViewConn
        
        # read data from file
        # content = open(portmaps_config, "r").read()
        gWebViewConn.run_js(f'setWebsocketUri("{self.websocketuri}")')
        # gWebViewConn.run_js('loadSettings("{}", {})'.format(portmaps_config, json.dumps(content)))
        gWebViewConn.run_js('reconnect()')

    def upload_program(self, content):
        uploadProgram(content)

if __name__ == "__main__":
    # import pydevd
    # pydevd.settrace('localhost', port=5678, stdoutToServer=True, stderrToServer=True)

    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,
                        datefmt="%H:%M:%S")

    parser = argparse.ArgumentParser(description='settings can be configurable by a settings.conf')
    parser.add_argument('--settings', nargs='?', help='settings file', default="settings.conf")
    args = parser.parse_args()    
    
    Settings.set(args.settings)

    portconfjson = None
    # if default robot file exists
    DEFAULT_ROBOT_FILE = 'robot_confs/default_portmaps.conf'
    if os.path.exists(DEFAULT_ROBOT_FILE):
        with open(DEFAULT_ROBOT_FILE, 'r') as f:
            portconfjson = json.loads(f.read())
    
    gWebViewConn = WebViewConn(WebviewAPI(), portconfjson)
    gWebViewConn.run('FSCONNECTOR', './main.html')
