import json
import asyncio
from asyncua import ua

class VrcCli:
    def __init__(self, portconf, opcua_conn, opcuasettings):
        self.opcua_conn = opcua_conn
        # self.opcua_settings = opcua_settings
        self.opcua_ns = opcuasettings['Namespace']
  
        self.registerPortmapsToOpcua(portconf)

    def _registerNode(self, portmaps):
        for jport in portmaps['Joints']:
            idx = "{}.{}".format(self.opcua_ns, jport["Name"])
            self.opcua_conn.registerNode(idx, jport["Name"], float(jport["Val"]), ua.VariantType.Double)
                
        for out in portmaps['OutputPorts']:
            idx = "{}.{}".format(self.opcua_ns, out["Name"])
            # if Type attribute in out exists, register as Int32
            if 'Type' in out and out['Type'] == 'Int32':
                self.opcua_conn.registerNode(idx, out["Name"], out['Val'], ua.VariantType.Int32)
            else:
                self.opcua_conn.registerNode(idx, out["Name"], False)
        
        for inport in portmaps['InputPorts']:
            idx = "{}.{}".format(self.opcua_ns, inport["Name"])
            # if Type attribute in inport exists, register as Int32
            if 'Type' in inport and inport['Type'] == 'Int32':
                self.opcua_conn.registerNode(idx, inport["Name"], 0, ua.VariantType.Int32)
            else:
                self.opcua_conn.registerNode(idx, inport["Name"], False)

    def registerPortmapsToOpcua(self, portmapconf):
        self.portmaps = portmapconf #json.load(open(portmapconf))
        self._registerNode(self.portmaps)
        self.HOST = self.portmaps['HOST'] if 'HOST' in self.portmaps else '127.0.0.1'
        self.PORT = self.portmaps['PORT'] if 'PORT' in self.portmaps else 30003
        self.FREQ = self.portmaps['FREQ'] if 'FREQ' in self.portmaps else 20

    async def publishToOpcua(self, joints, inputs, outputs):
        if self.opcua_conn is None: return
        idx_arr = []
        values = []
        
        if joints is not None:
            for jport in self.portmaps['Joints']:
                idx = "{}.{}".format(self.opcua_ns, jport["Name"])
                i = jport["Index"]
                
                idx_arr.append(idx)
                values.append(joints[i])
                # try:
                #     i = jport["Index"]
                #     await self.opcua_conn.writeValue(idx, joints[i])
                # except Exception as e:
                #     pass
            try:
                await self.opcua_conn.writeArrayValues(idx_arr, values)
            except Exception as e:
                pass
        
        idx_arr = []
        values = []
        if outputs is not None:
            for out in self.portmaps['OutputPorts']:
                # check is out has "Type" attribute
                if 'Type' in out and out['Type'] == 'Int32':
                    continue

                idx = "{}.{}".format(self.opcua_ns, out["Name"])
                p = int(out["Address"][1:]) # sanitize prefix
                val = int(outputs) >> p & (1)
                
                idx_arr.append(idx)
                values.append(bool(val))
                # try:
                #     await self.opcua_conn.writeValue(idx, bool(val))
                # except Exception as e:
                #     pass
            
            try:
                await self.opcua_conn.writeArrayValues(idx_arr, values)
            except Exception as e:
                pass


        idx_arr = []
        values = []
        if inputs is not None:
            for inp in self.portmaps['InputPorts']:
                idx = "{}.{}".format(self.opcua_ns, inp["Name"])
                p = int(inp["Address"][1:]) # sanitize prefix
                val = int(inputs) >> p & (1)
                
                idx_arr.append(idx)
                values.append(bool(val))
                # try:
                #     await self.opcua_conn.writeValue(idx, bool(val))
                # except Exception as e:
                #     pass
                
            try:
                await self.opcua_conn.writeArrayValues(idx_arr, values)
            except Exception as e:
                pass