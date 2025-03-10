
class Settings {
    static SETTING_FILE = '';
    static CONFIG = {};

    static loadPortmapXML(xmlString) {
        // Parse the XML string
        const parser = new DOMParser();
        const xmlDoc = parser.parseFromString(xmlString, "text/xml");

        // Retrieve the ControllerPort from "ControllerInputPorts" and "ControllerOutputPorts"
        const inputPortsNodes = xmlDoc.querySelectorAll('ControllerPorts ControllerInputPorts ControllerPort');
        const outputPortsNodes = xmlDoc.querySelectorAll('ControllerPorts ControllerOutputPorts ControllerPort');

        const input_ports = Array.from(inputPortsNodes).map(port => {
            return {
                'Name': port.getAttribute('Name'),
                'Address': port.getAttribute('Address')
            };
        }).filter(port => port.Name !== "");

        const output_ports = Array.from(outputPortsNodes).map(port => {
            return {
                'Name': port.getAttribute('Name'),
                'Address': port.getAttribute('Address')
            };
        }).filter(port => port.Name !== "");

        return {
            "ControllerName": "PLC",
            "InputPorts": input_ports,
            "OutputPorts": output_ports,
            "Joints": []
        };
    }

    static loadPortmap(filename, content) {
        const extension = filename.split('.').pop();
        if (extension == 'xml') {
            return Settings.loadPortmapXML(content);
        } else {
            try {
                return JSON.parse(content);
            } catch (error) {
                console.error("Error parsing JSON", error);
            }
        }
    }
}

// To use the function, you'd call:
// let parsedData = Settings.loadPortmapXML(xmlString);

function createPortsFromJsonstring(jsonString) {
    PORT_MAPS_CONF = JSON.parse(jsonString);
    createPorts(PORT_MAPS_CONF);
}

function createPorts(portmaps) {
    portmaps['OutputPorts'].forEach(out => {
        addSwitchElement(out['Name'], out['Address'])
        //sendOpcuaMessage('add', out['Name'], 'False');
    });
    portmaps['InputPorts'].forEach(inp => {
        addLampElement(inp['Name'], inp['Address'])
        //sendOpcuaMessage('add', inp['Name'], 'False');
    });
    portmaps['Joints'].forEach(jport => {
        addSliderElement(jport['Name'], jport['Min'], jport['Max'], jport['Val'])
        //sendOpcuaMessage('add', jport['Name'], '0.0');
    });

    pywebview.api.createPorts(portmaps);
    
        // if (ovar instanceof OPCUAFloatPort) {
    //   sendOpcuaMessage('add', ovar.varname, '0.0');
    // } else { //if  (var instanceof OPCUABooleanPort) {
    //   sendOpcuaMessage('add', ovar.varname, false);
    // }
    //document.getElementById('jsonFileInput').disabled = true;
    document.getElementById('start-button').disabled = false;
}

PORT_MAPS_CONF = null
let loadSettings = function(filename, content) {
    saved_port_maps_conf = PORT_MAPS_CONF
    PORT_MAPS_CONF = Settings.loadPortmap(filename, content);
    if (typeof PORT_MAPS_CONF === "object") {
        // merge the saved port maps with the new port maps
        
        createPorts(PORT_MAPS_CONF);
        if (saved_port_maps_conf != null) {
            PORT_MAPS_CONF['InputPorts'] = PORT_MAPS_CONF['InputPorts'].concat(saved_port_maps_conf['InputPorts']);
            PORT_MAPS_CONF['OutputPorts'] = PORT_MAPS_CONF['OutputPorts'].concat(saved_port_maps_conf['OutputPorts']);
            PORT_MAPS_CONF['Joints'] = PORT_MAPS_CONF['Joints'].concat(saved_port_maps_conf['Joints']);
        }
        
    } else {
        console.error("Unexpected JSON structure.");
    }
}

document.getElementById('jsonFileInput').addEventListener('change', function(event){
    const file = event.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const content = e.target.result;
            // check if the file type is xml
            const extension = file.name.split('.').pop();
            loadSettings(file.name, content)
        };

        reader.readAsText(file);
    }
});

let _websocketuri = 'ws://127.0.0.1:8000';
let websocket = new WebSocket(_websocketuri);
function setWebsocketUri(websocketuri) {
    _websocketuri = websocketuri
}

function reconnect() {
    pywebview.api.reconnect();
    websocket = new WebSocket(_websocketuri);
    
    // Listen for messages
    websocket.addEventListener("message", ({ data }) => {
        // alert(jointportsList)

        const event = JSON.parse(data);
       if (inputportsList.includes(event.varname) || outputportsList.includes(event.varname)) {
            updateBooleanPort(event.varname, event.val);
        } else if (jointportsList.includes(event.varname)) {
            updateJointPort(event.varname, event.val);
        }
    });
}

let lampsContainer = document.getElementById('lampsContainer');
let switchContainer = document.getElementById('switchContainer');
let jointsContainer = document.getElementById('jointsContainer');


let inputportsList = []
let outputportsList = []
let jointportsList = []

// javascript implement javascript websocket send message function

function sendMessage(message) {
    websocket.send(message);
}


const SERVER_NAMESPACE = 'ns=4;s=FSCONNECTOR.';
const useOpcuaWebsocket = true
const sendOpcuaMessage = (cmd, varname, val = false) => {
    if (typeof val == 'number') {
        useOpcuaWebsocket ? 
        sendMessage(JSON.stringify({'cmd': cmd, 'idx':SERVER_NAMESPACE + varname, 'name': varname, 'val':Number(val).toFixed(1)}))
            : pywebview.api.update_joint(varname, val); 
    } else if (typeof val == 'boolean') {
        useOpcuaWebsocket ? 
        sendMessage(JSON.stringify({'cmd': cmd, 'idx':SERVER_NAMESPACE + varname, 'name': varname, 'val':val}))   
        : pywebview.api.button_clicked(varname, val);            
    }
    // updateMessage(varname, val)
}


// Function to create and append a new lamp to the container
function addLampElement(name, address, val=false) {
    let newRoundContainer = document.createElement('div')
    newRoundContainer.classList.add('container')
    newRoundContainer.classList.add('lamp-round-container')

    let newLamp = document.createElement('div');
    newLamp.id = name;
    newLamp.classList.add('lamp');
    let associatedLabel = document.createElement('span');
    associatedLabel.classList.add('lamp-label');
    associatedLabel.innerText = name;
    
    newRoundContainer.appendChild(newLamp)
    newRoundContainer.appendChild(associatedLabel);
    
    lampsContainer.appendChild(newRoundContainer);

    inputportsList.push(name);
};

function addSwitchElement(name, address, val=false) {
    let newRoundContainer = document.createElement('div')
    newRoundContainer.classList.add('container')
    newRoundContainer.classList.add('switch-round-container')

    let newSwitch = document.createElement('label');
    newSwitch.classList.add('switch');
    newSwitch.id = address


    let newSwitchInput = document.createElement('input');
    newSwitchInput.classList.add('switch-checkbox');
    newSwitchInput.type = 'checkbox';
    newSwitchInput.id = name;
    newSwitchInput.checked = val;
    newSwitch.appendChild(newSwitchInput);

    let newSwitchSlider = document.createElement('span');
    newSwitchSlider.classList.add('slider');
    newSwitch.appendChild(newSwitchSlider);

    
    let associatedLabel = document.createElement('span');
    associatedLabel.classList.add('switch-label');
    associatedLabel.innerText = name;

    newRoundContainer.appendChild(newSwitch);
    newRoundContainer.appendChild(associatedLabel);
    switchContainer.appendChild(newRoundContainer);
    
    newSwitchInput.addEventListener('click', function() {
        handleUserInteraction();
        //pywebview.api.button_clicked(this.id, this.checked);
        //this.checked = !this.checked; // delay change until response from server
        sendOpcuaMessage('write', this.id, this.checked);

        // Stop listening to all ports to prevent instant reversion
        stopListenAllPorts();

        // Introduce a delay before re-validating the background status update
        delay(3000); // 3000 milliseconds delay

        // Re-validate the background status update
        readPortValue(this.id, false);

        // Start listening to all ports again
        startListenAllPorts();
    });

    outputportsList.push(name);
}


let SLIDER_VELOCITY = 1

function addSliderElement(name, min=0, max=255, defaultVal=0) {
    let sliderContainer = document.createElement('div');
    sliderContainer.classList.add('jointsContainer-container');


    let label = document.createElement('label');
    label.classList.add('jointslider-label');
    label.innerText = name
    sliderContainer.appendChild(label);

    let slider = document.createElement('input');
    slider.id = name;
    slider.type = 'range';
    slider.min = min;
    slider.max = max;
    slider.value = defaultVal;
    slider.classList.add('jointslider');
    sliderContainer.appendChild(slider);

    let sliderValue = document.createElement('input');
    sliderValue.classList.add('jointslider-value');
    sliderValue.value = '0';
    sliderValue.id = name + '-value'
    sliderContainer.appendChild(sliderValue);


    let decreaseButton = document.createElement('button');
    decreaseButton.innerText = '-';
    decreaseButton.id = name + '-decrease-button'
    sliderContainer.appendChild(decreaseButton);


    let increaseButton = document.createElement('button');
    increaseButton.innerText = '+';
    increaseButton.id = name + '-increase-button'
    sliderContainer.appendChild(increaseButton);

    jointsContainer.appendChild(sliderContainer);

    let associatedLabel = document.createElement('div');
    associatedLabel.classList.add('jointslider-label');
    jointsContainer.appendChild(associatedLabel);

    let sliderWriteLock = false;
    let syncJointValue = function(slider) {
        let jointValue = parseInt(slider.value);
        sliderValue.textContent = jointValue;
        
        if (sliderWriteLock) {
            return;
        }

        sliderWriteLock = true;
        //pywebview.api.update_joint(slider.id, jointValue);
        sendOpcuaMessage('write', slider.id, jointValue);
        
        // setTimeout(function () {
        //     if (slider.value != jointValue) { // update the slider if the value has changed
        //         pywebview.api.update_joint(slider.id, jointValue);
        //     }
        //     sliderWriteLock = false;
        // }, 50);
        sliderWriteLock = false;
    };

    let range = max - min

    let increaseJointValue = function(slider) {
        handleUserInteraction();
        scale = range < 6000 ? 1 : range/6000;
        slider.value = Math.min(max, parseInt(slider.value) + 1*SLIDER_VELOCITY*scale);
        sliderValue.value = slider.value;
        syncJointValue(slider);
    };

    let decreaseJointValue = function(slider) {
        handleUserInteraction();
        slider.value = Math.max(min, parseInt(slider.value) - 1*SLIDER_VELOCITY*scale);
        sliderValue.value = slider.value;
        syncJointValue(slider);
    };

    // Events
    slider.addEventListener('input', function() {
        sliderValue.value = this.value;
        syncJointValue(slider);
    });

    sliderValue.addEventListener('change', function() {
        
        handleUserInteraction();
        
        value = parseInt(this.value);
        if (isNaN(value)) {
            sliderValue.value = slider.value;
            return;
        }

        value = Math.min(max, parseInt(this.value));
        value = Math.max(min, value);
        slider.value = value;
        sliderValue.value = value;
        syncJointValue(slider);
        
    });

    decreaseButton.addEventListener('click', decreaseJointValue.bind(null, slider));

    increaseButton.addEventListener('click', increaseJointValue.bind(null, slider));
    
    decreaseButton.addEventListener('mousedown', function() {
        let interval = setInterval(decreaseJointValue.bind(null, slider), 50);
        decreaseButton.addEventListener('mouseup', function() {
            clearInterval(interval);
        });
    });

    increaseButton.addEventListener('mousedown', function() {
        let interval = setInterval(increaseJointValue.bind(null, slider), 50);
        increaseButton.addEventListener('mouseup', function() {
            clearInterval(interval);
        });
    });

    jointportsList.push(name);
}

// start a ticking timer for A

let timerA = null;
let timerAStart = null;
let timerB = null;
let timerBStart = null;

function startTimerA() {
    if (timerA != null) {
        return;//clearInterval(timerA);
    }

    timerAStart = Date.now();
    timerA = setInterval(function() {
        let timeNow = Date.now();
        let timeDiff = timeNow - timerAStart;
        let timeDiffMiniseconds = timeDiff % 1000;
        let timeDiffSec = Math.floor(timeDiff/1000);
        let timeDiffMin = Math.floor(timeDiff/60000);
        let timeDiffHr = Math.floor(timeDiff/3600000);
        let timeDiffStr = timeDiffSec.toString().padStart(2, '0') + '.' + timeDiffMiniseconds.toString().padStart(3, '0');
        if (timeDiffMin > 0) {
            timeDiffStr = timeDiffMin.toString().padStart(2, '0') + ':' + timeDiffStr;
        }
        if (timeDiffHr > 0) {
            timeDiffStr = timeDiffHr.toString().padStart(2, '0') + ':' + timeDiffStr;
        }
        document.getElementById('RunningA-Time').innerText = timeDiffStr;
    }, 1000);
}

function startTimerB() {
    if (timerB != null) {
        return; //clearInterval(timerB);
    }

    timerBStart = Date.now();
    timerB = setInterval(function() {
        let timeNow = Date.now();
        let timeDiff = timeNow - timerBStart;
        let timeDiffMiniseconds = timeDiff % 1000;
        let timeDiffSec = Math.floor(timeDiff/1000);
        let timeDiffMin = Math.floor(timeDiff/60000);
        let timeDiffHr = Math.floor(timeDiff/3600000);
        
        let timeDiffStr = timeDiffSec.toString().padStart(2, '0') + '.' + timeDiffMiniseconds.toString().padStart(3, '0');
        if (timeDiffMin > 0) {
            timeDiffStr = timeDiffMin.toString().padStart(2, '0') + ':' + timeDiffStr;
        }
        if (timeDiffHr > 0) {
            timeDiffStr = timeDiffHr.toString().padStart(2, '0') + ':' + timeDiffStr;
        }
        document.getElementById('RunningB-Time').innerText = timeDiffStr;
    }, 1000);
}

function stopTimerA() {
    if (timerA != null) {
        clearInterval(timerA);
    }

    timerA = null;
    timerAStart = null;
    //document.getElementById('RunningA-Time').innerText = 'Stopped';
}

function stopTimerB() {
    if (timerB != null) {
        clearInterval(timerB);
    }

    timerB = null;
    timerBStart = null;
    //document.getElementById('RunningB-Time').innerText = 'Stopped';
}


function updateBooleanPort(name, val) {
    if (val) { 
        document.getElementById(name).classList.add('on');
    } else {
        document.getElementById(name).classList.remove('on');
    }
    if (val != document.getElementById(name).checked) {
        document.getElementById(name).classList.add('active')
        document.getElementById(name).checked = val;
    }

    if (name == 'RunningA') {
        if (val) {
            startTimerA();
        } else {
            stopTimerA();
        }

    } else if (name == 'RunningB') {
        if (val) {
            startTimerB();
        } else {
            stopTimerB();
        }
    }
}

function updateJointPort(name, val) {
    slider = document.getElementById(name)
    if (slider) {
        slider.value = val;
    }

    sliderval = document.getElementById(name+'-value')
    if (sliderval) {
        sliderval.value = val;
    }
}

function readPortValue(name, val) {
    // pywebview.api.refresh(name).then(function(response){
    //     res = JSON.parse(response)
        
    //     updateBooleanPort(name, res.val);
    
    // })
    sendOpcuaMessage('read', name, val);
}

function readAllPortValues(names) {
    if (names == null || names.length == 0) {
        return
    }

    for (let i = 0; i < names.length; i++) {
        //alert(names[i])
        readPortValue(names[i], false);
    }
    // pywebview.api.batch_refresh(names).then(function(response){
    //     allres = JSON.parse(response)
        
    //     for (let i = 0; i < allres.length; i++) {
    //         res = allres[i] 
    //         //alert(res)
    //         updateBooleanPort(names[i], res.val);
    //     }
    // })
}


function readInputPorts() {
    // loop readList to read all ports
    readAllPortValues(inputportsList)
}

function readOutputPorts() {
    readAllPortValues(outputportsList);
}

function listenJointPortValues() {
    readAllPortValues(jointportsList);
}

function listenIOPortValues() {
    readAllPortValues(inputportsList);
    readAllPortValues(outputportsList);
}

let listenJointInterval = null;
let listenIOInterval = null;
function stopListenAllPorts() {
    if (listenJointInterval != null) {
        clearInterval(listenJointInterval);
    }

    if (listenIOInterval != null) {
        clearInterval(listenIOInterval);
    }

    listenJointInterval = null;
    listenIOInterval = null;
}

function listenJointPorts() {
    listenJointInterval = setInterval(listenJointPortValues, 100)
    // listenJointPortValues()
}

function listenIOPorts() {
    listenIOInterval = setInterval(listenIOPortValues, 1000);
    // listenIOPortValues()
}

function startListenAllPorts() {
    listenJointPorts();
    listenIOPorts();
    document.getElementById('listen-button').classList.add('on');
}

function stopListenAllPorts() {
    stopListenAllPorts();
    document.getElementById('listen-button').classList.remove('on');
}

function toggleListenAllPorts() {
    if (listenJointInterval == null) {
        startListenAllPorts();
    } else {
        stopListenAllPorts();
    }
}

// Function to introduce a delay
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}
// Example of how to use the delay function
async function handleUserInteraction() {
    // Perform user interaction logic here
    // ...
    // Update the UI
    stopListenAllPorts();

    // Introduce a delay before updating the UI
    await delay(1000); // 500 milliseconds delay

    // Update the UI
    startListenAllPorts();
}



function mapKeys(keymaps, event) {
    keymaps.forEach((km) => {
        if (event.key == km.key) {
            //alert(km.id)
            document.getElementById(km.id).click()
            return
        }
    });
}

document.addEventListener("keydown", (event) => {
    console.log(`key=${event.key},code=${event.code}`);
    if (event.code == 'ShiftLeft') {
        SLIDER_VELOCITY = 10
    } else if (event.code == 'ShiftRight') {
        SLIDER_VELOCITY = 1
    } 
    
    mapKeys([
        {key: 'k', id: 'Z-decrease-button'},
        {key: 'i', id: 'Z-increase-button'},
        {key: 'j', id: 'Y-decrease-button'},
        {key: 'l', id: 'Y-increase-button'},
        {key: 's', id: 'A-decrease-button'},
        {key: 'w', id: 'A-increase-button'},
        {key: 'a', id: 'Rz-decrease-button'},
        {key: 'd', id: 'Rz-increase-button'},
        {key: 'g', id: 'X-decrease-button'},
        {key: 'h', id: 'X-increase-button'},
    ], event)
});

/*document.addEventListener("keyup", (event) => {
    console.log(`key=${event.key},code=${event.code}`);
    if (event.key == 'Shift') {
        SLIDER_VELOCITY = 1
    }
});*/

function startListening() {

    document.getElementById('start-button').classList.add('on');
    document.getElementById('listen-button').disabled = false;
    document.getElementById('jsonFileInput').disabled = true;
    // gray document.getElementById('jsonFileInput')
    document.getElementById('jsonFileInput').classList.add('disabled');
    // remove hover effect input[type=file]::file-selector-button:hover
    document.getElementById('jsonFileInput').classList.add('no-hover::file-selector-button');
}

function start() {
    // robot = document.getElementById('robotList').value;
    pywebview.api.start(JSON.stringify(PORT_MAPS_CONF)).then(function(response){
        res = JSON.parse(response)

        startListening();
    })

}

function uploadProgram() { // Only available for UR robots
    // pywebview.api.upload_program().then(function(response){
    //     res = JSON.parse(response)
    // })
    // Create an input element
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = '.script'; // Specify the file types you want to accept

    // Add an event listener to handle the file selection
    input.addEventListener('change', function(event) {
        const file = event.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                const content = e.target.result;
                // Handle the file content here
                console.log(content);
                // You can send the file content to the backend if needed
                pywebview.api.upload_program(content).then(function(response){
                    res = JSON.parse(response);
                });
            };
            reader.readAsText(file);
        }
    });

    // Trigger the file input dialog
    input.click();
}