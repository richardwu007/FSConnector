
from conn_vrc.ur_connector import URConnector
from conn_vrc.ur_web_cli import URWebCli

from conn_vrc.siasun_connector import SiasunConnector
from conn_vrc.siasun_web_cli import SiasunWebCli
from conn_vrc.step_proxy_connector import StepProxyConnector
from conn_vrc.step_proxy_web_cli import StepProxyWebCli

from conn_vrc.kuka_connector import KukaConnector
from conn_vrc.otc_connector import OtcConnector
from conn_opcua.conn_opcua_client import OpcuaClientConn

from conn_vrc.plc_cli import PLCCli

from conn_vrc.keber_conveyor_cli import KeberConveyorCli
from conn_vrc.keber_conveyor_connector import KeberConveyorConnector

from conn_vrc.vrc_cli import VrcCli
from conn_vrc.dual_machine_cli import DualMachineCli
from conn_vrc.dual_machine_connector import DualMachineConnector

from conn_vrc.rexroth_connector import RexrothConnector

from conn_web.conn_api import app
from conn_opcua.conn_opcua_server import OpcuaServerConn
from conn_web.conn_websocket import WebSocketConn

from settings import Settings

OPCUA_SERVER = OpcuaServerConn()
__vrc_conn = None

def runOpcuaServer(serverStartedCallback=None):
    print("Starting OPCUA Server")
    opcuasettings = Settings.readOPCUAServerConfig()
    OPCUA_SERVER.start_server(opcua_namespace=opcuasettings['Namespace'], host=opcuasettings['HOST'], port=opcuasettings['PORT'], serverupCallback=serverStartedCallback)
    

def stopOpcuaServer(serverStoppeddCallback = None):
    OPCUA_SERVER.stop_server()

    # if vrc_conn is not None: vrc_conn.stop_server()
    if serverStoppeddCallback is not None: serverStoppeddCallback()


def uploadProgram(content):
    __vrc_conn.upload_program(content)

def runVRCServer(portconf): # callback when the opcua server is up and running
    global __vrc_conn
    opcuasettings = Settings.readOPCUAServerConfig()
    vrc_conn = None

    opcua_conn = OpcuaClientConn(opcuasettings['HOST'], opcuasettings['PORT']) 
    
    if portconf['Manufacturer'] == "UNIVERSAL":
        ur_client = URWebCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = URConnector(host=ur_client.HOST, opcua_conn=opcua_conn, opcuasettings=opcuasettings, port=ur_client.PORT, freq=ur_client.FREQ)
        vrc_conn.subscribe(ur_client.process)
        vrc_conn.start_server()
        
    elif portconf['Manufacturer'] == "SIASUN":
        client = SiasunWebCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = SiasunConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.subscribe(client.process)
        vrc_conn.start_server()
        
    elif portconf['Manufacturer'] == "STEP_PROXY":
        client = StepProxyWebCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = StepProxyConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.subscribe(client.process)
        vrc_conn.start_server()
                
    elif portconf['Manufacturer'] == "KUKA":
        client = VrcCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = KukaConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.start_server()
        
    elif portconf['Manufacturer'] == "OTC":
        client = VrcCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = OtcConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.start_server()

    elif portconf['Manufacturer'] == "PLC":
        client = PLCCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        client.registerPortmapsToOpcua(portconf)
        opcua_conn.start_server()

    elif portconf['Manufacturer'] == "KEBER":
        client = KeberConveyorCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = KeberConveyorConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.subscribe(client.process)
        vrc_conn.start_server()
    elif portconf['Manufacturer'] == "DUAL_MACHINE":
        client = DualMachineCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = DualMachineConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.subscribe(client.process)
        vrc_conn.start_server()
    elif portconf['Manufacturer'] == "REXROTH":
        opcua_conn = OpcuaClientConn(opcuasettings['HOST'], opcuasettings['PORT'])
        client = VrcCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        vrc_conn = RexrothConnector(opcua_conn=opcua_conn, opcuasettings=opcuasettings, host=client.HOST, port=client.PORT, freq=client.FREQ)
        vrc_conn.start_server()
    else:
        client = PLCCli(portconf=portconf, opcua_conn=opcua_conn, opcuasettings=opcuasettings)
        client.registerPortmapsToOpcua(portconf)
        opcua_conn.start_server()

    __vrc_conn = vrc_conn

    # start websocket server
    opcua_conn = OpcuaClientConn(opcuasettings['HOST'], opcuasettings['PORT'])
    websocketsettings = Settings.readWebSocketServerConfig()
    websocketserver = WebSocketConn(websocketsettings, opcua_conn)
    websocketserver.start_server()