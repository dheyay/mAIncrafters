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

## temporary until reimplementation of dijkstra's
from priority_dict import priorityDictionary
##

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
            self.agent_host.parse(sys.argv)
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)

        # Agent's current_position:
        self.x_pos = 0
        self.y_pos = 0

        # Agent's "home" panel
        self.x_home = 0
        self.y_home = 0

        # Add observation space and search/action space accordingly


        # Keeping track of the current_shortest path; assuming we want to go back to x_home, y_home
            ## since we haven't handled actions yet, blank for now. But the plan is to either have
            ## the dijkstra algorithm apply at the end (in which case we'd want some kind of record
            ## of where we've been so far), or simply keep track of the current offset from center.
            ## for example, if we're at 5, 7, the shortest path (in discrete) is the route along
            ## 5, 7. Then if we move up to 5, 6, we'd just remove a north movement, so that the shortest
            ## route is now along 5, 6. Effectively, we'd have two stacks of directions. Using the
            ## North/South stack as an example: Say we move north. Peek at the top element of the stack.
            ## If the stack is empty, push N. If the stack has an S at the top, pop it. If the stack has
            ## an N at the top, push the N. Same for east/west. Then, when we want to return, simply pop
            ## all the elements of the stacks until empty. We can also work in a version of this where
            ## we use dijkstra's on a smaller observation. While we maintain the shortest path as above,
            ## we may may encounter a mountain or something in the z dimension that wasn't accounted for
            ## when the shortest path was being calculated. We can then use dijkstra's on the observation
            ## available to find the shortest path to /the closest recently visited space/, and then resume
            ## popping the stack items. Under this model, we'd want to make sure the agent never strays
            ## further than the observation window's distance from the travelled path when returning.
            ## We may also want to consider a vertical "limit", in the sense that we consider any blocks
            ## or block towers with a height above "x" is considered untraversable.

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
        my_clients.add(MalmoPython.ClientInfo('127.0.0.1', 10000))  # add Minecraft machines here as available

        for retry in range(max_retries):
            try:
                self.agent_host.startMission(my_mission, my_clients, my_mission_record, 0, 'SteverCrafter')
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
               "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size,
                                                                                               self.size, self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(self.size, self.size,
                                                                                               self.size, -self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size,
                                                                                               -self.size, -self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='fence'/>".format(-self.size, -self.size,
                                                                                               -self.size, self.size) + \
               "<DrawCuboid x1='{}' x2='{}' y1='3' y2='3' z1='{}' z2='{}' type='air'/>".format(-self.size, self.size,
                                                                                               -self.size, self.size) + \
               "<DrawCuboid x1='{}' x2='{}' y1='1' y2='1' z1='{}' z2='{}' type='grass'/>".format(-self.size, self.size,
                                                                                                 -self.size,
                                                                                                 self.size) + \
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
                <min x="-''' + str(int(self.obs_size)) + '''" y="0" z="-''' + str(int(self.obs_size)) + '''"/>
                            <max x="''' + str(int(self.obs_size)) + '''" y="0" z="''' + str(int(self.obs_size)) + '''"/>
                          </Grid>
                      </ObservationFromGrid>
                    </AgentHandlers>
                  </AgentSection>
                </Mission>'''

    def load_grid(self, world_state):
        while world_state.is_mission_running:
            # sys.stdout.write(".")
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

    def dijkstra_shortest_path(self, grid_obs, source, dest):
        """
        Finds the shortest path from source to destination on the map. It used the grid observation as the graph.
        See example on the Tutorial.pdf file for knowing which index should be north, south, west and east.

        Args
            grid_obs:   <list>  list of block types string representing the blocks on the map.
            source:     <int>   source block index.
            dest:       <int>   destination block index.

        Returns
            path_list:  <list>  block indexes representing a path from source (first element) to destination (last)
        """
        prio_dict = priorityDictionary()
        prio_dict[source] = 0
        iterator = iter(prio_dict)
        current_best_length = dict()
        for i in range(len(grid_obs)):
            current_best_length[i] = (float('inf'), None)
        current_best_length[source] = (0, None)

        while True:
            try:
                current_space = next(iterator)
            except StopIteration:
                break

            if current_space + self.obs_size*2 < len(grid_obs) and \
                    current_best_length[current_space][0] + 1 < current_best_length[current_space + 21][0] and \
                    grid_obs[current_space + self.obs_size*2] != "air" and \
                    current_space != current_best_length[current_space + self.obs_size*2][1]:

                current_best_length[current_space + self.obs_size*2] = (current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space + self.obs_size*2] = current_best_length[current_space + self.obs_size*2][0]


            if current_space + 1 < len(grid_obs) and \
                    current_best_length[current_space][0] + 1 < current_best_length[current_space + 1][0] and \
                    grid_obs[current_space + 1] != "air" and \
                    current_space != current_best_length[current_space + 1][1]:

                current_best_length[current_space + 1] = (current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space + 1] = current_best_length[current_space + 1][0]


            if current_space - 1 >= 0 and \
                    current_best_length[current_space][0] + 1 < current_best_length[current_space - 1][0] and \
                    grid_obs[current_space - 1] != "air" and \
                    current_space != current_best_length[current_space - 1][1]:

                current_best_length[current_space - 1] = (current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space - 1] = current_best_length[current_space - 1][0]


            if current_space - self.obs_size*2 >= 0 and \
                    current_best_length[current_space][0] + 1 < current_best_length[current_space - self.obs_size*2][0] and \
                    grid_obs[current_space - self.obs_size*2] != "air" and \
                    current_space != current_best_length[current_space - self.obs_size*2][1]:
                current_best_length[current_space - self.obs_size*2] = (current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space - self.obs_size*2] = current_best_length[current_space - 1][0]

        best_path = [dest]
        prev = dest
        while prev != source:
            prev = current_best_length[prev][1]
            best_path.append(prev)

        best_path.reverse()

        return (best_path)

    def extract_action_list_from_path(self, path_list):
        """
        Converts a block idx path to action list.

        Args
            path_list:  <list>  list of block idx from source block to dest block.

        Returns
            action_list: <list> list of string discrete action commands (e.g. ['movesouth 1', 'movewest 1', ...]
        """
        action_trans = {-self.obs_size*2: 'movenorth 1', self.obs_size*2: 'movesouth 1', -1: 'movewest 1', 1: 'moveeast 1'}
        alist = []
        for i in range(len(path_list) - 1):
            curr_block, next_block = path_list[i:(i + 2)]
            alist.append(action_trans[next_block - curr_block])

        return alist


    def get_return_path(self, world_state):

        grid = self.load_grid(self, world_state)

        current_location_index = self.obs_size*2*(self.y_pos+50) + self.x_pos + 50
        home_index = self.obs_size*2*(self.y_home+50) + self.x_home + 50
        
        shortest_path = self.dijkstra_shortest_path(grid, current_location_index, home_index)
        action_list = self.extract_action_list_from_path(shortest_path)

        return action_list




if __name__ == '__main__':
    Steve = SteverCrafter()
    world = Steve.init_malmo()
    print((Steve.load_grid(world)))
