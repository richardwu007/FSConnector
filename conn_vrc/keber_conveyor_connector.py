import logging
import socket
from collections import deque
import asyncio
from tkinter import filedialog
from pubsub import pub
import threading
from conn_vrc.vrc_connector import VRCConnector
from conn_vrc.ur_uploader_util import URUtil
from conn_opcua.conn_opcua_client import OpcuaClientConn, BaseClientSubHandler

import numpy as np

class KeberConveyor():
    class ConveyorNode():
        def __init__(self, pos):
            self.position = np.array(pos)

        def setPos(self, pos):
            self.position[0] = pos[0]
            self.position[1] = pos[1]

    def __init__(self, state_positions=[]):
        self.state_positions = np.array(state_positions)
        self.node_num = len(state_positions)
        self.buildConveyorStateMachine(state_positions)
        self.current_state = 0

    # build a conveyor state machine and create N nodes to represent the conveyor
    def buildConveyorStateMachine(self, node_positions = []):
        # each node will be defined its position and the state machine will be built
        self.conveyor_nodes = []
        for i in range(len(node_positions)):
            node = self.ConveyorNode(node_positions[i])
            self.conveyor_nodes.append(node)
    
    
    def moveConveyorToNextNode(self, node, currpos, nextpos, total_steps=100):
            
        # Calculate the difference between the target position and the current position
        # target_position_difference =  self.state_positions[(i+1)%len(self.state_positions)] - self.state_positions[i]
        target_position_difference =  nextpos - currpos
        
        # Calculate the step size for each motion
        step_size = target_position_difference / total_steps
        
        # Create a list of motions for this node
        motions = [node.position + step_size * step for step in range(1, total_steps + 1)]
        
        # move each node's position to the next target node's position
        node.setPos(nextpos)
        
        return motions

    def forwardUpperConveyorMotions(self, total_steps=100):
        node_motions = []
        # move each node's position to the next target node's position
        for i in range(5):
            node = self.conveyor_nodes[i]

            motions = self.moveConveyorToNextNode(node, node.position, self.state_positions[(i+1)%len(self.state_positions)], total_steps) 
            node_motions.append(motions)

        return node_motions

    def backwardUpperConveyor(self, total_steps=100):
        node_motions = []
        # move each node's position to the next target node's position
        for i in range(5):
            node = self.conveyor_nodes[i]

            motions = self.moveConveyorToNextNode(node, node.position, self.state_positions[(i)%len(self.state_positions)], total_steps) 
            node_motions.append(motions)

        return node_motions


    def forwardLowerConveyorMotions(self, total_steps=100):
        node_motions = []
        # move each node's position to the next target node's position
        for i in range(6, 10):
            node = self.conveyor_nodes[i]

            motions = self.moveConveyorToNextNode(node, node.position, self.state_positions[(i+1)%len(self.state_positions)], total_steps) 
            node_motions.append(motions)

        return node_motions

    def backwardLowerConveyor(self, total_steps=100):
        node_motions = []
        # move each node's position to the next target node's position
        for i in range(6, 10):
            node = self.conveyor_nodes[i]

            motions = self.moveConveyorToNextNode(node, node.position, self.state_positions[(i)%len(self.state_positions)], total_steps) 
            node_motions.append(motions)

        return node_motions

class KeberConveyorConnector(VRCConnector):
    
    def __init__(self, opcua_conn, opcuasettings, host = "127.0.0.1", port = 30003, freq = 60):
        VRCConnector.__init__(self, opcua_conn, opcuasettings, host, port, freq)

        self.state_positions = [
            (0, 0),                 #MP1 S1 S2
            (0, 1440.000),          #MP2 S3 S4
            (0, 2790.000),          #MP3 S5 S6
            (0, 4878.498),          #MP4 S7 S8
            (0, 6193.498),          #MP5 S9 S10
            (0, 7924.498),          #MP6 S11 S12
            (-591.044, 7924.498),   #MP7 S13 S14
            (-591.044, 6193.498),   #MP8 S15 S16
            (-591.044, 4878.498),   #MP9 S17 S18
            (-591.044, 2790.000),   #MP10 S19 S20
            (-591.044, 0)    #
        ]

        self.conveyor = KeberConveyor(self.state_positions)
        self.current_step = 0

    async def connect(self):
        await self.opcua_conn.connect()

    async def processRotateReq(self):
        req = await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.ReqRotate")
        req2 = await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.GrantRotate")
        req = req or req2

        if req:
            await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.AckRotateCompleted", False)
            return True

        return False
    
    async def processResetReq(self):
        return await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.ReqReset")

    async def processPreloadReq(self):
        return await self.opcua_conn.readValue("ns=4;s=FSCONNECTOR.ReqPreload")

    async def completedRotateReq(self):
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.GrantRotate", False)
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.AckRotateCompleted", True)
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.ReqRotate", False)

        # rotate right-shift the state_positions
        # self.state_positions = np.roll(self.state_positions, -1,  axis=0)

    async def _moveConveyor(self, node_motions, joint_ids):
        for step in range(len(node_motions[0])):
            # get the joints of the current step of each node, and flatten the array
            joints = [motion[step] for motion in node_motions]
            inputs = []
            outputs = []
            
            # flatten the array into a one-dimension array
            joints = np.array(joints).flatten()
            # map each joint_ids and joints into a list of tuples
            joints = [[joint_ids[i], joints[i]] for i in range(len(joint_ids))]

            # joints = [[f"S{i+1}", joints[i]] for i in range(10)]
          
            await self.publish([joints, inputs, outputs])
            await self.idle()
            await self.idle()

    async def moveUpperConveyorToNextNode(self, total_steps=100):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.MP1", 
                                                "ns=4;s=FSCONNECTOR.MP2", 
                                                "ns=4;s=FSCONNECTOR.MP3", 
                                                "ns=4;s=FSCONNECTOR.MP4",
                                                "ns=4;s=FSCONNECTOR.MP5"], 
                                               [True, True, True, True, True])

        node_motions = self.conveyor.forwardUpperConveyorMotions(total_steps)
        await self._moveConveyor(node_motions, ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"))
        await asyncio.sleep(1)

    async def rewindUpperConveyor(self, total_steps=5):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.MP1", 
                                                "ns=4;s=FSCONNECTOR.MP2", 
                                                "ns=4;s=FSCONNECTOR.MP3", 
                                                "ns=4;s=FSCONNECTOR.MP4",
                                                "ns=4;s=FSCONNECTOR.MP5"], 
                                               [False, False, False, False, False])

        node_motions = self.conveyor.backwardUpperConveyor(total_steps)
        await self._moveConveyor(node_motions, ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10"))

        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Load", False)

    async def moveLowerConveyorToNextNode(self, total_steps=50):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.MP7", 
                                                "ns=4;s=FSCONNECTOR.MP8", 
                                                "ns=4;s=FSCONNECTOR.MP9", 
                                                "ns=4;s=FSCONNECTOR.MP10"], 
                                               [True, True, True, True])

        node_motions = self.conveyor.forwardLowerConveyorMotions(total_steps)
        await self._moveConveyor(node_motions, ("S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20"))
        await asyncio.sleep(2)

    async def rewindLowerConveyor(self, total_steps=5):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.MP7", 
                                                "ns=4;s=FSCONNECTOR.MP8", 
                                                "ns=4;s=FSCONNECTOR.MP9", 
                                                "ns=4;s=FSCONNECTOR.MP10"], 
                                               [False, False, False, False])
        
        node_motions = self.conveyor.backwardLowerConveyor(total_steps)
        await self._moveConveyor(node_motions, ("S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20"))
        await asyncio.sleep(2)
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Unload", False)

    async def loadWorkpiece(self):
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Source1 TriggerMaterial", True)
        await asyncio.sleep(1)
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Source1 TriggerMaterial", False)
        await asyncio.sleep(1)

        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Load", True)
        await asyncio.sleep(2)

        # select the loading fixture by the current step
        loaded_fixture = (8 - self.current_step) % 8 + 1
        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.MP1_1221A-{loaded_fixture}_WP", True)
        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.122A1-{loaded_fixture}Toggle", True)
        await asyncio.sleep(2)

        self.current_step = (self.current_step + 1) % 8
        
    async def unloadWorkpiece(self):
         # select the loading fixture by the current step
        unloaded_fixture = (8 - self.current_step - 3) % 8 + 1
        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.MP1_1221A-{unloaded_fixture}_WP", False)
        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.122A1-{unloaded_fixture}Toggle", False)
        await asyncio.sleep(2)


        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Unload", True)
        await asyncio.sleep(5)


    async def triggerRobots(self):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.TriggerRobot1",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot2",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot3",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot4",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot5",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot6",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot7",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot8"], 
                                               [True, True, True, True, True, True, True, True])
        await asyncio.sleep(1)
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.TriggerRobot1",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot2",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot3",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot4",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot5",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot6",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot7",
                                                "ns=4;s=FSCONNECTOR.TriggerRobot8"], 
                                               [False, False, False, False, False, False, False, False])

    async def weldWorkpiece(self):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.YDJG1_Toggle",
                                                 "ns=4;s=FSCONNECTOR.YDJG2_Toggle",
                                                 "ns=4;s=FSCONNECTOR.YDJG3_Toggle",
                                                 "ns=4;s=FSCONNECTOR.YDJG4_Toggle"], 
                                               [True, True, True, True])
        await asyncio.sleep(1)
        await self.triggerRobots()


    async def weldComplted(self):
        await self.opcua_conn.writeArrayValues(["ns=4;s=FSCONNECTOR.YDJG1_Toggle",
                                                 "ns=4;s=FSCONNECTOR.YDJG2_Toggle",
                                                 "ns=4;s=FSCONNECTOR.YDJG3_Toggle",
                                                 "ns=4;s=FSCONNECTOR.YDJG4_Toggle"], 
                                               [False, False, False, False])
        await asyncio.sleep(1)
        
    async def proceed(self):
        await self.loadWorkpiece()
        await self.moveUpperConveyorToNextNode(100)
        await self.weldWorkpiece()
        await self.rewindUpperConveyor()
        await self.weldComplted()
        await self.unloadWorkpiece()
        await self.moveLowerConveyorToNextNode(100)
        await self.rewindLowerConveyor()
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.ReqRotate", False)
        

    async def _preloadWorkpiece(self, fixture, joint):
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Source1 TriggerMaterial", True)
        await asyncio.sleep(1)
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.Source1 TriggerMaterial", False)
        
        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.MP{fixture}", True)

        await self.publish([[[joint, 0.00]], None, None])
        await asyncio.sleep(1)

        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.MP1_1221A-{fixture}_WP", True)
        await self.opcua_conn.writeValue(f"ns=4;s=FSCONNECTOR.122A1-{fixture}Toggle", True)

        await self.publish([[[joint, 2000.00]], None, None])
        
    async def resetFixtures(self):
        joint_ids = ("S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "S10", 
                "S11", "S12", "S13", "S14", "S15", "S16", "S17", "S18", "S19", "S20")
        positions = np.array(self.state_positions).flatten()
        joints = [[joint_ids[i], positions[i]] for i in range(len(joint_ids))]
        await self.publish([joints, None, None])
        await asyncio.sleep(1)

    async def preload(self):
        
        await self._preloadWorkpiece(2, "S4")
        await self._preloadWorkpiece(3, "S6")
        await self._preloadWorkpiece(4, "S8")
        await self._preloadWorkpiece(5, "S10")

        await self.resetFixtures()

        await asyncio.sleep(2)
        await self.triggerRobots()
        await asyncio.sleep(2)
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.ReqPreload", False)

    async def reset(self):
        for node in self.opcua_conn.regNodes:
            await self.opcua_conn.writeValue(node[0], node[2])

        await self.resetFixtures()
        await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.ReqReset", False)

    async def listen(self):
        #await self.opcua_conn.writeValue("ns=4;s=FSCONNECTOR.ReqRotate", True)
        await self.connect()
        await self.resetFixtures()


        while self.STOP_SERVER is False:
            try:
                shouldReset = await self.processResetReq()
                if shouldReset:
                    await self.reset()

                reqPreload = await self.processPreloadReq()
                if reqPreload:
                    await self.preload()

                reqRotate = await self.processRotateReq()
                if reqRotate:
                    await self.proceed()
                    
                    await self.completedRotateReq()
                    await asyncio.sleep(2)

                await self.idle()
            except Exception as e:
                logging.error('socket receiving exception')
                await self.connect()
