# FASTSUITE OPCUA Connector for UR CB Series

FASTSUITE supports OPCUA connectors to communicate with robot controllers. 
This example demonstrates a digital twin workstation that mirrors a real station equipped with a Deprag screwing tool, an ITEM table, and an UR robot on the KIT GAMI premises. 

Hardware Specs:
- UR 5
- CB Controller
- Deprag Controller
- Deprag Screwing Tool
- Deprag Screwfeeder
- ITEM Table

Downloads:
- [UR Scenario Cendoc](https://internal.fastsuite.cn/DEPRAG/ESTUN_UR_OPCUA.cendoc)
- [FSConnector-v0.1](https://internal.fastsuite.cn/DEPRAG/FSConnector-v0.1.7z)


** Credit goes to Global Advanced Manufacturing Institute (GAMI), Karlsruhe Institue of Technology.

# Process of Building a Digital Twin

## CONCEPT PHASE
* Import mechanical design CAD and build workcell equipment
* Build the workpiece
* Build the Deprag tool resource
    - Define the kinematics
    - Define the screw snap adaptor
    - Create the Source-and-Sink adaptor to feed screws
* Map the Deprag tool electric ports to UR
    - Define the Resource Behavior signal mapping
    - Remap the controller logic out ports
        - Match the port mappings according to the tool electric specs `电气连接口.xlsx`
        - ** Be careful to drag-and-snap incidents to mess up the previous mapping, E2 will always remap them sequencially
* Create collision groups and associate them to validate collision advoidance
* Activate the controller and the `Screwing` technology and start to program
* Drag and select target point PGs on the hole matrix of the workpiece, make a challenging screwing sequence of a irregular shape or a form of characters or so...

## DETAILING PHASE

### Screw Events & Translator
Screwing signal interaction and associated events are packed and handled by the `ScrewOnEvent` and `ScrewOffEvent` events which are defined in the `Deprag Plugin` to signal the tool resource. And use `UNIVERSAL_CB3_SCRIPT_Deprag.xml` translator to generate Deprag screwing commands in the final program.   

### Optimize Toolpath Sequences
* Program the screwing toolpaths and validate/rearrange the layout.
* Use the `Plugin` to insert screw events on the approach and retract points.
* Select the plugin translator to interpret screw events in the program code.
* Simulate the detailed process of feeding screws and fixate them on the target positions.
* Optimize the toolpath sequences and analyze the cycletime.
* Simulate again then download the program.

## COMMISSIONING PHASE - Software in the Loop

At the commissioning phase, the qualified program is ready to commission in the virtual world. The equipment behaviors, either mechanic or electric, are simulated by its "digital twin". In this case, the UR robot present by its simulator URSim.

To run the URSim robot simulator, navigate the link to download the virtual machine [https://www.universal-robots.com/download/software-cb-series/simulator-non-linux/offline-simulator-cb-series-non-linux-ursim-3143/](https://www.universal-robots.com/download/software-cb-series/simulator-non-linux/offline-simulator-cb-series-non-linux-ursim-3143/)

* Run UR Robot on URSim Simulator
    - Steps to Setup on the VirtualBox
        * Configure the network to use physical bridge network 
        * Launch URSim 5 
        * Enable EtherNet
        * Find the IP address of the URSim

<video class="iframe_video" src="https://internal.fastsuite.cn/DEPRAG/SetupURSimVirtualBox.mp4" controls ></video>


### Run the Python FSConncetor
FSConnector runs a OPCUA server and a client to bridge the communication between the Fastsuite and URSim.

* Open the `settings.conf` file to configure connectors, the configurations are defined in a JSON fashion.
  Its objects and attributes are described as follow:

* `OPCUAServer`: OPCUA server connection
* `WebSocketServer`: Websocket server connection
```
{

    "OPCUAServer":
    {
        "HOST": "127.0.0.1",
        "PORT": 4842,
        "Namespace":"ns=4;s=FSCONNECTOR"
    },
     "WebSocketServer": {
        "HOST": "127.0.0.1",
        "PORT": 8080
    }
}
``` 


`PortMapConf` refers the robot configuration, which defines 

* `HOST`: IP to connect to either the robot. 
* `PORT`: of the remote control port
* `InputPorts`: maps the input ports of the address and the OPCUA variable name
* `OutputPorts`: maps the output ports of the address and the OPCUA variable name
* `Joints`: maps the joints and the OPCUA variable name
```
{
    "Manufacturer": "UNIVERSAL",
    "ControllerName": "UR",
    "HOST": "192.168.239.128",
    "PORT": 30003,
    "FREQ": 60,
    "InputPorts":[],
    "OutputPorts": 
        [{"Address":"Q1",
        "Name":"GunScrewing"},
        {"Address":"Q3",
        "Name":"MP_Screw"},
        {"Address":"Q5",
        "Name":"GunThrustMin"},
        {"Address":"Q6",
        "Name":"GunThrustMax"},
        {"Address":"Q7",
        "Name":"FeedScrew"}
        ],
    "Joints":
        [
       {"Index": 0,
        "Name": "D1",
        "Min": -360.0,
        "Max": 360.0,
        "Val": 90.001
        },
        {"Index": 1,
        "Name": "D2",
        "Min": -360.0,
        "Max": 360.0,
        "Val": -25.504
        },
        {"Index": 2,
        "Name": "D3",
        "Min": -360.0,
        "Max": 360.0,
        "Val": 30.366
        },
        {"Index": 3,
        "Name": "D4",
        "Min": -360.0,
        "Max": 360.0,
        "Val": 0.000
        },
        {"Index": 4,
        "Name": "D5",
        "Min": -360.0,
        "Max": 360.0,
        "Val": 85.318
        },
        {"Index": 5,
        "Name": "D6",
        "Min": -90.0,
        "Max": 90.0,
        "Val": 90.003
        }
        ]
}
```


### Connect and Upload Program to UR
Launch `FSConnector.exe`, then click `RUN` button, the UR connection is estabilished. Click `LOAD PROGRAM` to upload a script program to the UR.

### Setup E2 VRC Controller
Navigate to the `Controller Builder` module in E2, select the UR control, click the `Simulator/Connector Settings` button and create a OPCUA connector and fill its properties.
![resources/e2controlleropcua](https://internal.fastsuite.cn/DEPRAG/e2controlleropcua.png)

### Run Everything in SIL 
<video class="iframe_video" src="https://internal.fastsuite.cn/DEPRAG/RunFSConnector.mp4" controls ></video>


## Operating Phase - Hardware in the Loop
Since the digital twin has been built and validated in the SIL stage, time to commission to the real world.

### Calibration
To be done..

### Run HIL
<video class="iframe_video" src="https://internal.fastsuite.cn/DEPRAG/UR_DigitalTwin.mp4" controls ></video>

## Known Issues
* After running for a long while, the `FSConnector` fails to pick up data from the UR and doesn't repond to E2.
    * https://stackoverflow.com/questions/72382790/python-opc-ua-client-stops-reading-after-a-while
    * Possible root causes:
        - 1-) Ex. in kepserverex opc server runtime has 2 hour for a free version. then it ill stoped read data and publish to opc server. Maybe other opc servers are like this.
        - 2-) OPC servers include some config settings like connection time or alive time or someting like that. Check your server settings.
        - 3-) Some Opc servers need certificate, if u connect wihout certificate it ill close session after a while for security.
        - 4-) Sometimes our request failed from server , because server cant read data of your wish. This error can lead to logging out, it can also be in the configuration settings of this server.

* asyncua 0.8.4 vs 0.9.94
    * In 0.8.4, writing node value is faster. In 0.9.94, one write_value operation can take up to few seconds.  

* Asyncua client behavior has been changed to retain the connection, under `asyncua\client\client.py` python file
    ```async def __aexit__(self, exc_type, exc_value, traceback):
        #await self.disconnect() # Richard modified
        pass
    ```

## Compile Python Source
* Select the python version to activate its virtual env `python -m venv venv`. A different version requires its distinct compiled pyc files.
### under src folder
python -m venv venv
.\venv\Scripts\activate
python -m pip install --upgrade pip
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

### Python 3.10 avoids the websocket connection issues
C:\Users\wu_cc\AppData\Local\Programs\Python\Python310\Scripts\pyinstaller.exe -p C:\Users\wu_cc\AppData\Local\Programs\Python\Python310\Lib\site-packages  --onefile --windowed --icon=Fastsuite_E2_Icon.ico -p http -p webview -p websockets   -p asyncio -p asyncua -p conn_opcua -p conn_vrc -p conn_web --add-data "main.html;." --add-data "main.js;."  --add-data "Fastsuite_E2_Icon.ico;." --add-data "webview;webview"  FSConnector.py