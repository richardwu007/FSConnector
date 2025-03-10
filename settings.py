import json
import xml.etree.ElementTree as ET
import os

class Settings:
    SETTING_FILE = ''
    CONFIG = {
        "Connectors":[
        {}
        ],
        
        "OPCUAServer": {
            "HOST": "127.0.0.1",
            "PORT": 4842,
            "Namespace":"ns=4;s=FSCONNECTOR"
        },
        "WebSocketServer": {
            "HOST": "127.0.0.1",
            "PORT": 8000
        }
    }

    @staticmethod
    def loadPortmapXML(xml_file):

        # Load and parse the XML file
        tree = ET.parse(xml_file)
        root = tree.getroot()

        
        # Retrieve the ControllerPort from "ControllerInputPorts" and "ControllerOutputPorts"
        input_ports = [{'Name':port.get('Name'), 'Address':port.get('Address')} for port in root.findall('.//ControllerPorts/ControllerInputPorts/ControllerPort') if port.get('Name') != ""]
        output_ports = [{'Name':port.get('Name'), 'Address':port.get('Address')} for port in root.findall('.//ControllerPorts/ControllerOutputPorts/ControllerPort') if port.get('Name') != ""]
        
        return {"ControllerName": "PLC","InputPorts": input_ports, "OutputPorts": output_ports, "Joints": []}

    @staticmethod 
    def readOPCUAServerConfig():
        return Settings.CONFIG["OPCUAServer"]

    @staticmethod 
    def readConnectorsConfig():
        return Settings.CONFIG["Connectors"]
    
    @staticmethod 
    def readWebSocketServerConfig():
        return Settings.CONFIG["WebSocketServer"]

    @staticmethod
    def set(conf):
        # check if conf file exists
        if not os.path.exists(conf):
            return # do nothing
        
        Settings.SETTING_FILE = conf
        Settings.CONFIG = json.load(open(conf))
        settings_new = {"Connectors": []}
        # for connector in Settings.CONFIG["Connectors"]:
        #     settings_new['Connectors'].append( # parse portmap conf file
        #         {
        #             "Manufacturer": connector["Manufacturer"],
        #             # cehck if connector['PortMapConf'] file type is not xml
        #             "PortMapConf": json.load(open(connector['PortMapConf'])) if connector['PortMapConf'].split('.')[-1] != 'xml' else Settings.loadPortmapXML(connector['PortMapConf']), 
        #             "Namespace": connector["Namespace"]
        #         }
        #     )
        
        settings_new['OPCUAServer'] = Settings.CONFIG['OPCUAServer']
        settings_new['WebSocketServer'] = Settings.CONFIG['WebSocketServer']
        Settings.CONFIG = settings_new
        return Settings.CONFIG


    @staticmethod
    def readURConnSettings():
        try:
            settings = [connector for connector in Settings.CONFIG['Connectors'] if connector['Manufacturer'] == "UNIVERSAL"][0]
            return settings['PortMapConf']['HOST'], settings['PortMapConf']['PORT']
        except:
            return "127.0.0.1", "4842"
        
    @staticmethod
    def readKUKAConnSettings():
        try:
            settings = [connector for connector in Settings.CONFIG['Connectors'] if connector['Manufacturer'] == "KUKA"][0]
            return settings['PortMapConf']['HOST'], settings['PortMapConf']['PORT']
        except:
            return "127.0.0.1", "4842"

    
    @staticmethod
    def readDefaultSettings():
        try:
            settings = [connector for connector in Settings.CONFIG['Connectors']][0]
            return settings['PortMapConf']['HOST'], settings['PortMapConf']['PORT']
        except:
            return "127.0.0.1", "4842"


    @staticmethod
    def setAddr(host):
        settings = Settings.CONFIG['Connectors'][0]
        settings['PortMapConf']['HOST'] = host
        
        
if __name__ == "__main__":
    Settings.loadPortmapXML('./robot_confs/e2portmap.xml')