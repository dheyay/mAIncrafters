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

import random

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

        # Obstacles and material densities
        self.obstacle_density = 0.1

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

        # Agent's destination panel
        self.x_dest = self.size
        self.y_dest = self.size

        # "True" destinations, since the others are relative (useful for checking if the destination is reached)
        self.true_x_dest = self.size
        self.true_y_dest = self.size

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

        self.reverse = False
        # Return Stacks:
        self.x_return = []
        self.y_return = []
        self.x_return_index = 0
        self.y_return_index = 0
        self.is_x_return = True

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
        obstacles = []
        for i in range(-self.size, self.size):
            for j in range(-self.size, self.size):
                if random.random() < self.obstacle_density:
                    obstacles.append((i, j))

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
                      <FlatWorldGenerator generatorString="3;7,59*1,3*3,2;1;stronghold,biome_1(distance=32)" forceReset="1"/>
                       <DrawingDecorator>''' + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size, self.size, self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(self.size, self.size, self.size, -self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size, -self.size, -self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(-self.size, -self.size, -self.size, self.size) + \
               ''.join(["<DrawBlock x='{}' y='64' z='{}' type='wool'/>".format(x[0], x[1]) for x in obstacles]) + \
               "<DrawBlock x='{}' y='64' z='{}' type='log' />".format(randint(-self.size, self.size), randint(-self.size, self.size)) + \
               "<DrawBlock x='{}' y='64' z='{}' type='log' />".format(randint(-self.size, self.size), randint(-self.size, self.size)) + \
               '''
          </DrawingDecorator>
          <ServerQuitWhenAnyAgentFinishes/>
        </ServerHandlers>
      </ServerSection>
      <AgentSection mode="Survival">
        <Name>MainCrafterBoi</Name>
        <AgentStart>
            <Placement x="0.5" y="64" z="0.5" pitch="45" yaw="0"/>
            <Inventory>
                <InventoryItem slot="0" type="diamond_pickaxe"/>
            </Inventory>
        </AgentStart>
        <AgentHandlers>
            <DiscreteMovementCommands/>
            <ObservationFromFullStats/>
            <ObservationFromRay/>
            <ObservationFromGrid>
              <Grid name="floorAll">
                <min x="-''' + str(int(self.obs_size)) + '''" y="-1" z="-''' + str(int(self.obs_size)) + '''"/>
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

    def block_action(self, world_state, block_type):
        allow_break_action = False

        if world_state.is_mission_running:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            print(world_state)
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')

            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)

                sight_block = observations['LineOfSight']['type']

                if (sight_block != block_type):
                    self.agent_host.sendCommand('turn 1')

                print(sight_block)
                if (sight_block == block_type):
                    self.agent_host.sendCommand('attack 1')

        return allow_break_action

        # self.agent_host.sendCommand('move 1') # move one ahead to make sure you collect

    ## CONSIDERED EDIT: CREATE A LIST/DICT OF "BANNED" BLOCKS, SUCH AS LAVA OR AIR,
    ## THE THE AGENT AVOIDS WHEN LOOKING AT A PATH.

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

            if current_space + (self.obs_size * 2 + 1) < len(grid_obs)//2 and \
                    current_best_length[current_space][0] + 1 < \
                    current_best_length[current_space + (self.obs_size * 2 + 1)][0] and \
                    grid_obs[current_space + (self.obs_size * 2 + 1)] != "air" and \
                    grid_obs[current_space + (((2 * self.obs_size) + 1) ** 2) + (self.obs_size * 2 + 1)] != "wool" and \
                    current_space != current_best_length[current_space + (self.obs_size * 2 + 1)][1]:
                current_best_length[current_space + (self.obs_size * 2 + 1)] = (
                    current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space + (self.obs_size * 2 + 1)] = \
                    current_best_length[current_space + (self.obs_size * 2 + 1)][0]

            if current_space + 1 < len(grid_obs)//2 and \
                    current_best_length[current_space][0] + 1 < current_best_length[current_space + 1][0] and \
                    grid_obs[current_space + 1] != "air" and \
                    grid_obs[current_space + (((2 * self.obs_size) + 1) ** 2) + 1] != "wool" and \
                    current_space != current_best_length[current_space + 1][1]:
                current_best_length[current_space + 1] = (current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space + 1] = current_best_length[current_space + 1][0]

            if current_space - 1 >= 0 and \
                    current_best_length[current_space][0] + 1 < current_best_length[current_space - 1][0] and \
                    grid_obs[current_space - 1] != "air" and \
                    grid_obs[current_space + (((2 * self.obs_size) + 1) ** 2) - 1] != "wool" and \
                    current_space != current_best_length[current_space - 1][1]:
                current_best_length[current_space - 1] = (current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space - 1] = current_best_length[current_space - 1][0]

            if current_space - (self.obs_size * 2 + 1) >= 0 and \
                    current_best_length[current_space][0] + 1 < \
                    current_best_length[current_space - (self.obs_size * 2 + 1)][0] and \
                    grid_obs[current_space - (self.obs_size * 2 + 1)] != "air" and \
                    grid_obs[current_space + (((2 * self.obs_size) + 1) ** 2) - (self.obs_size * 2 + 1)] != "wool" and \
                    current_space != current_best_length[current_space - (self.obs_size * 2 + 1)][1]:
                current_best_length[current_space - (self.obs_size * 2 + 1)] = (
                    current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space - (self.obs_size * 2 + 1)] = current_best_length[current_space - 1][0]

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
        action_trans = {-(self.obs_size * 2 + 1): 'movenorth 1', (self.obs_size * 2 + 1): 'movesouth 1',
                        -1: 'movewest 1',
                        1: 'moveeast 1'}
        alist = []
        for i in range(len(path_list) - 1):
            curr_block, next_block = path_list[i:(i + 2)]
            alist.append(action_trans[next_block - curr_block])

        return alist

    def find_destination(self, grid_obs, destination_block):
        """
        Finds the source and destination block indexes from the list.
        Args
            grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)
        Returns
            start: <int>   source block index in the list
            end:   <int>   destination block index in the list
        """

        ## from Stack overflow: https://stackoverflow.com/questions/398299/looping-in-a-spiral
        def spiral(X, Y):
            x = y = 0
            dx = 0
            dy = -1
            for i in range(max(X, Y) ** 2):
                if (-X / 2 < x <= X / 2) and (-Y / 2 < y <= Y / 2):
                    # print("location: ", x, y)
                    # print("block at location: ", grid_obs[4*(self.obs_size**2) + self.obs_size * 2 * (y + 50) + x + 50])
                    # print("destination_block: ", destination_block)
                    if grid_obs[(((2 * self.obs_size) + 1) ** 2) + (self.obs_size * 2 + 1) * (
                            50 + y) + 50 + x] == destination_block:
                        return x, y
                if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                    dx, dy = -dy, dx
                x, y = x + dx, y + dy

        return spiral(2 * self.obs_size, 2 * self.obs_size)

    def get_shortest_path(self, world_state, destination_block):

        grid = self.load_grid(world_state)

        # print(grid)

        if (destination_block == "air"):
            destination_index = (self.obs_size * 2 + 1) * (50 - self.y_pos) + 50 - self.x_pos
            self.true_x_dest = 0
            self.true_y_dest = 0

        else:
            results = self.find_destination(grid, destination_block)

            print("Results: ", results)

            if results == None:
                self.reverse = True
                return []
                # destination_index = self.obs_size * 2 * (self.y_home + 50) + self.x_home + 50
            else:
                destination_x, destination_y = results[0], results[1]

                # print("x_destination: ", destination_x)
                # print("y_destination: ", destination_y)

                destination_index = (self.obs_size * 2 + 1) * (destination_y + 50) + destination_x + 50
                self.true_x_dest = self.x_pos + destination_x
                self.true_y_dest = self.y_pos + destination_y

        current_location_index = (self.obs_size * 2 + 1) * 50 + 50
        # home_index = self.obs_size * 2 * (self.y_home + 50) + self.x_home + 50
        # destination_index = self.obs_size * 2 * (self.y_dest + 50) + self.x_dest + 50

        shortest_path = self.dijkstra_shortest_path(grid, current_location_index, destination_index)
        action_list = self.extract_action_list_from_path(shortest_path)

        return action_list

    def update_return_path(self, action):
        if action == "moveeast 1":
            if len(self.x_return) == 0:
                self.x_return.append("movewest 1")
            else:
                if self.x_return[-1] == "moveeast 1":
                    self.x_return.pop()
                else:
                    self.x_return.append("movewest 1")

        elif action == "movewest 1":
            if len(self.x_return) == 0:
                self.x_return.append("moveeast 1")
            else:
                if self.x_return[-1] == "movewest 1":
                    self.x_return.pop()
                else:
                    self.x_return.append("moveeast 1")

        elif action == "movesouth 1":
            if len(self.y_return) == 0:
                self.y_return.append("movenorth 1")
            else:
                if self.y_return[-1] == "movesouth 1":
                    self.y_return.pop()
                else:
                    self.y_return.append("movenorth 1")

        elif action == "movenorth 1":
            if len(self.y_return) == 0:
                self.y_return.append("movesouth 1")
            else:
                if self.y_return[-1] == "movenorth 1":
                    self.y_return.pop()
                else:
                    self.y_return.append("movesouth 1")

    def agent_near_dest(self):
        if abs(self.x_pos - self.true_x_dest) <= 1 and abs(self.y_pos - self.true_y_dest) == 0 or \
                abs(self.x_pos - self.true_x_dest) == 0 and abs(self.y_pos - self.true_y_dest) <= 1:
            return True
        else:
            return False


if __name__ == '__main__':
    print("Starting...")
    Steve = SteverCrafter()
    world_state = Steve.init_malmo()

    block = "log"

    action_index = 0
    ## At this point, we'll need to have determined what our destination is.
    ## Air is the default that will just send it to the default destination,
    ## but if a block is generated in the world and that type is specified,
    ## can use that instead and it will get the path to that block
    action_list = Steve.get_shortest_path(world_state, "log")
    # print(action_list)
    temp = 1

    while world_state.is_mission_running:
        # sys.stdout.write(".")
        time.sleep(0.1)

        ## Here, we would have any destination updates. The commented-out code is
        ## an example of what going to a new location might look like, while the
        ## code left in is what the final return branch would look like when
        ## taking the shortest path back.
        ## For reference, when we are using the observation, we are going to want to convert
        ## indices as 50 + x + obs_size * ((50 + z) + obs_size*obs_size, which will have us
        ## accessing the first layer above ground ( and generally, we have
        ## 50 + x + obs_size*2 * ((50 + z) + obs_size*obs_size*4*(layer above) for the observation
        ## space of a given layer, assuming we asked for it in the XML. Layer above = 0 is the ground,
        ## which is why when converting in the path find logic, we drop the obs_size*obs_size.

        if Steve.agent_near_dest() and Steve.reverse == False:
            print("Found block")
            allow_break = Steve.block_action(world_state, block)
            ## if the agent has reached within a space of the destination;
            ## -----------------------------------------------------------
            ##
            ## Code for dealing with the block would go here
            ##
            ## -----------------------------------------------------------
            # Steve.do_break_action(allow_break, block_sight, block)

            ## We also may want a flag of sorts here that determines if the action is a
            ## movement or not, since the

            ## Then, depending on what we're looking for, go for the next closest item:
            ## Here, I just assume we're only mining diamond ore. In reality, we'd
            ## probably want a list/data structure with the items we want, which would
            ## function here

            ## Just find the next diamond_ore:
            action_index = 0
            action_list = Steve.get_shortest_path(world_state, block)
            print("reverse: ", Steve.reverse)
            print("Finding new block: ", action_list)
            time.sleep(1)

            ## if there are no diamond ore in the observation view, Steve.reverse will be
            ## set to true, and action_list will be empty
            if Steve.reverse == True:
                ##Steve.x_return.extend(Steve.y_return)
                ##action_list = Steve.x_return
                action_list = Steve.get_shortest_path(world_state, "air")
                #Steve.is_x_return = True

        else:
            # Sending the next commend from the action list -- found using the Dijkstra algo.
            if action_index >= len(action_list):
                print("Error:", "out of actions, but mission has not ended!")

                time.sleep(2)
                action_index = -1
                action_list = Steve.get_shortest_path(world_state, block)
                #print("true x_dest:", Steve.true_x_dest)
                #print("true y dest:", Steve.true_y_dest)
                print(Steve.agent_near_dest())

                if action_list != []:
                    print("Haha, jk, I'm getting another block")
                    Steve.reverse = False



            else:

                ## If the agent is not yet on it's return journey, any movement it takes is
                ## used to update the return path
                #if Steve.reverse == False:
                    #Steve.update_return_path((action_list[action_index]))

                ## We may want code that deals with any obstacles in the agent's way as well,
                ## Since it's possible that the return path gets blocked
                ## I also want to update the dijkstra's algorithm to avoid obstacles, but that's getting
                ## too invested in Dijkstra's when we will be replacing it with a search eventually.
                #if Steve.open_direction(action_list[action_index]) == False:
                #    if Steve.is_x_return:
                #        Steve.is_x_return = False
                #        Steve.x_return_index = action_index
                #        action_index = Steve.y_return_index
                #    else:
                #        Steve.is_x_return = True
                #        Steve.y_return_index = action_index
                #        action_index = Steve.x_return_index



                if action_list[action_index] == "moveeast 1":
                    Steve.x_pos += 1
                elif action_list[action_index] == "movewest 1":
                    Steve.x_pos -= 1
                elif action_list[action_index] == "movesouth 1":
                    Steve.y_pos += 1
                elif action_list[action_index] == "movenorth 1":
                    Steve.y_pos -= 1

                print("x_pos: ", Steve.x_pos)
                print("y_pos: ", Steve.y_pos)
                print("sending command: ", action_list[action_index])
                Steve.agent_host.sendCommand(action_list[action_index])

            action_index += 1

            #if len(action_list) == action_index:
                # Need to wait few seconds to let the world state realise I'm in end block.
                # Another option could be just to add no move actions -- I thought sleep is more elegant.
            #    time.sleep(2)

            world_state = Steve.agent_host.getWorldState()

            for error in world_state.errors:
                print("Error:", error.text)
