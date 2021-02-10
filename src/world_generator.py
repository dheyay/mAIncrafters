# ------------------------------------------------------------------------------------------------
# Copyright (c) 2016 Microsoft Corporation
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and
# associated documentation files (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge, publish, distribute,
# sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or
# substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT
# NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
# DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
# ------------------------------------------------------------------------------------------------

try:
    from malmo import MalmoPython
except:
    import MalmoPython

import sys
import time
import json
import matplotlib.pyplot as plt
import numpy as np
from numpy.random import randint

import gym, ray
from gym.spaces import Discrete, Box
from ray.rllib.agents import ppo

class SteverCrafter():
    
    def __init__(self):
        # World size
        self.size = 50
        self.obs_size = 50
        
        # Malmo Parameters
        self.agent_host = MalmoPython.AgentHost()
        try:
            self.agent_host.parse( sys.argv )
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)
        
        # Add observation space and search/action space accordingly 
        
    def init_malmo(self):
        """
        Initialize new malmo mission.
        """
        my_mission = MalmoPython.MissionSpec(self.GetMissionXML(), True)
        my_mission_record = MalmoPython.MissionRecordSpec()
        my_mission.requestVideo(800, 500)
        my_mission.setViewpoint(1)

        max_retries = 3
        my_clients = MalmoPython.ClientPool()
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000)) # add Minecraft machines here as available

        for retry in range(max_retries):
            try:
                self.agent_host.startMission( my_mission, my_clients, my_mission_record, 0, 'DiamondCollector' )
                break
            except RuntimeError as e:
                if retry == max_retries - 1:
                    print("Error starting mission:", e)
                    exit(1)
                else:
                    time.sleep(2)

        world_state = self.agent_host.getWorldState()
        while not world_state.has_mission_begun:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            for error in world_state.errors:
                print("\nError:", error.text)

        return world_state
    
    def GetMissionXML(self):
        return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
    
                  <About>
                    <Summary>Hello world!</Summary>
                  </About>
    
                <ServerSection>
                  <ServerInitialConditions>
                    <Time>
                        <StartTime>1000</StartTime>
                        <AllowPassageOfTime>false</AllowPassageOfTime>
                    </Time>
                    <Weather>clear</Weather>
                  </ServerInitialConditions>
                  <ServerHandlers>
                      <FlatWorldGenerator generatorString="3;7,2;1;"/>
                       <DrawingDecorator>''' + \
                          "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size, self.size, self.size) + \
                          "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(self.size, self.size, self.size, -self.size) + \
                          "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size, -self.size, -self.size) + \
                          "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(-self.size, -self.size, -self.size, self.size) + \
                          "<DrawCuboid x1='{}' x2='{}' y1='3' y2='3' z1='{}' z2='{}' type='air'/>".format(-self.size, self.size, -self.size, self.size) + \
                          "<DrawCuboid x1='{}' x2='{}' y1='1' y2='1' z1='{}' z2='{}' type='grass'/>".format(-self.size, self.size, -self.size, self.size) + \
                           '''
                      </DrawingDecorator>
                      <ServerQuitWhenAnyAgentFinishes/>
                    </ServerHandlers>
                  </ServerSection>
    
                  <AgentSection mode="Creative">
                    <Name>MainCrafterBoi</Name>
                    <AgentStart>
                        <Placement x="0.5" y="2" z="0.5" pitch="45" yaw="0"/>
                    </AgentStart>
                    <AgentHandlers>
                        <DiscreteMovementCommands/>
                        <ObservationFromGrid>
                          <Grid name="floorAll">
                            <min x="-'''+str(int(self.obs_size))+'''" y="0" z="-'''+str(int(self.obs_size))+'''"/>
                            <max x="'''+str(int(self.obs_size))+'''" y="0" z="'''+str(int(self.obs_size))+'''"/>
                          </Grid>
                      </ObservationFromGrid>
                    </AgentHandlers>
                  </AgentSection>
                </Mission>'''
    
    def load_grid(self, world_state):
        while world_state.is_mission_running:
            #sys.stdout.write(".")
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')
    
            if world_state.number_of_observations_since_last_state > 0:
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                grid = observations.get(u'floorAll', 0)
                break
        return grid
    
if __name__ == '__main__':
    Steve = SteverCrafter()
    world = Steve.init_malmo()
    print((Steve.load_grid(world)))
        
        