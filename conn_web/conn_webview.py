import asyncio
import os
import sys
# sys.path.insert(0, "..")
import logging
import threading
from tkinter import PhotoImage, Tk
import webview
# from webview import api

from websockets.sync.client import connect
import json


logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger('webview')

# retain websocket


# class APIWebsocketConnect():
#     def __init__(self, api_obj):
#         self.api_obj = api_obj
    
#     def __enter__(self):
#         try:
#             if self.api_obj.websocket is None:
#                 self.api_obj.websocket = connect("ws://127.0.0.1:8000/", close_timeout=None, open_timeout=None)
#         except Exception as e:
#             print(e)
#             self.api_obj.websocket = None
        
#         return self.api_obj.websocket

#     def __exit__(self, *args):
#         pass # retain websocket
    
# class API:
    
#     def __init__(self):
#         # self.conn = conn
#         # self.window = window
#         self.websocket = None
    
#     def reconnect(self):
#         self.websocket = connect("ws://127.0.0.1:8000/", close_timeout=None, open_timeout=None)
#     # def connect_websocket(self):
#     #     self.websocket = connect("ws://127.0.0.1:8000/")
    
    
#     def send(self, data):
#         try:
#             self.websocket.send(data)
#         except Exception as e:
#             print(e)
#             self.reconnect()
#             self.websocket.send(data)
            
#     # @api
#     def item_selected(self, params):
#         selected_item = params
#         print(f"You selected: {selected_item}")
#         return "Item selected successfully"
    
#     def button_clicked(self, name, val):
#         print(f"You clicked: {name}")
        
#         with APIWebsocketConnect(self) as websocket:
#             req = {'cmd': 'write', 'idx': "ns=4;s=PLC_CELL.{}".format(name), 'name': name, 'val': val}
#             self.send(json.dumps(req))
#             # message = websocket.recv() # too frequent reads-and-writes cause opcua server to crash
#             # print(f"Received: {message}")
            

#         return "Button clicked successfully"

#     def refresh(self, name):
#         with APIWebsocketConnect(self) as websocket:
#             req = {'cmd': 'read', 'idx': "ns=4;s=PLC_CELL.{}".format(name), 'name': name}
#             self.send(json.dumps(req))
#             message = websocket.recv()
            
#             return message
        
#     def batch_refresh(self, names):
#         with APIWebsocketConnect(self) as websocket:
#             req = {'cmd': 'batch_read', 'idx': "ns=4;s=PLC_CELL", 'name': names}
#             self.send(json.dumps(req))
#             message = websocket.recv()
            
#             return message
        
#     def update_joint(self, name, val):
#         with APIWebsocketConnect(self) as websocket:
#         # if self.websocket is None:
#         #     self.connect_websocket()    
#             req = {'cmd': 'write', 'idx': "ns=4;s=PLC_CELL.{}".format(name), 'name': name, 'val': float(val)}
#             self.send(json.dumps(req)) # '{"cmd": "write", "idx": "ns=4;s=PLC_CELL.Rz", "name": "Rz", "val": 3.0}'
#             # message = websocket.recv()
#             # print(f"Received: {message}")
        
#     def createPorts(self, portmaps):
#         for jport in portmaps['Joints']:
#             req = {'cmd': 'add', 'idx': "ns=4;s=PLC_CELL.{}".format(jport["Name"]), 'name': jport["Name"], 'val': float(jport["Val"])}
#             self.send(json.dumps(req))
                
#         for out in portmaps['OutputPorts']:
#             req = {'cmd': 'add', 'idx': "ns=4;s=PLC_CELL.{}".format(out["Name"]), 'name': out["Name"], 'val': False}
#             self.send(json.dumps(req))
        
#         for inp in portmaps['InputPorts']:
#             req = {'cmd': 'add', 'idx': "ns=4;s=PLC_CELL.{}".format(inp["Name"]), 'name': inp["Name"], 'val': False}
#             self.send(json.dumps(req))

   
#     def start():
       
#        pass
   
   

class WebViewConn:
    def __init__(self, js_api, portmaps=None):
        self.future = asyncio.Future()
        self.portmaps = portmaps
        self.js_api = js_api
        
    def evaluate_js(self):
        self.createPorts(self.portmaps)
        # self.js_api.createPorts(self.portmaps)
        # result = self.window.evaluate_js(
        #     r"""
        #         startListening()

        #     """)
    
    def run_js(self, content):
        return self.window.evaluate_js(
            r"""
                {}

            """.format(content))
    
       
    def createPorts(self, portmaps):
        if portmaps is None:
            return
        
        result = self.window.evaluate_js(
                f'createPortsFromJsonstring(\'{json.dumps(portmaps)}\')'
        )
        
            
    def run(self, title='Default UI Title', url='listbutton.html', width=1500, height=960):
        #tk = Tk()
  
        #  size of the window where we show our website
        #tk.geometry("800x450")
        # set the favicon of the pywebview window
        #picFile = "CENIT_gross_RGB.png"
        # """ Get absolute path to resource, works for dev and for PyInstaller """
        #base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        self.window = webview.create_window(title, width=width, height=height, url=url, js_api=self.js_api)
        # self.window.gui.toggle_fullscreen()
        # pic = PhotoImage(file=os.path.join(base_path, picFile))
        # Icon set for program window
        # self.window.gui.iconphoto(False, pic)
        #tk.iconphoto(False, pic)
        
        # delay for 1 second
        import time
        time.sleep(1)
        webview.start(self.evaluate_js, debug=False)
    
    def run_webview_thread(client):
        client.run()
        
    def start_server(self):
        self.webview_th = threading.Thread(target=WebViewConn.run_webview_thread, args=(self,))
        self.webview_th.start()
        
    def stop(self):
        pass

if __name__ == '__main__':
    conn = WebViewConn()
    
    conn.start_server()