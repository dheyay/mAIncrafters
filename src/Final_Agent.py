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
import random

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

# from Recipes import ITEM_RECIPES, get_ingredients
import aStar


class SteverCrafter():

    def __init__(self):
        # World size
        self.size = 100
        self.obs_size = 100

        self.prob_matrix = dict()
        self.search = []
        # Malmo Parameters
        self.agent_host = MalmoPython.AgentHost()
        try:
            self.agent_host.parse(sys.argv)
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)

        self.crafting_list = ["ladder",'iron_sword','crafting_table']
        self.crafting_completed = False
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

        # For keeping track of the current block
        self.current_block = "air"

        # For the biome selection
        self.biome_dest = None

        # Probabilities used in creating the world:
        self.biome_probabilities = {"sand_biome": {"air": 0.97, "log": 0.01, "coal_ore": 0.01, "iron_ore": 0.01},
                                    "snow_biome": {"air": 0.97, "iron_ore": 0.03},
                                    "stone_biome": {"air": 0.97, "stone": 0.03},
                                    "default_biome": {"air": 0.97, "log": 0.03}}

        self.biome_cdfs = dict()

        for biome in self.biome_probabilities:
            current_cdf = 0
            self.biome_cdfs[biome] = dict()
            for material in self.biome_probabilities[biome]:
                current_cdf += self.biome_probabilities[biome][material]
                self.biome_cdfs[biome][current_cdf] = material

        #results in this with the default settings:

        '''self.biome_cdfs = {"first_biome": {0.98: "air", 1: "log"},
                           "second_biome": {0.98: "air", 1: "coal_ore"},
                           "third_biome": {0.98: "air", 1: "iron_ore"},
                           "fourth_biome": {0.98: "air", 1: "log"}}'''

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
        coordinates = [(1, 1, self.size, self.size), (-self.size, -self.size, -1, -1), (1, -self.size, self.size, -1),
                       (-self.size, 1, -1, self.size)]
        r = [0, 1, 2, 3]
        random.shuffle(r)

        stone_obstacles = ''
        cactus_obstacles = ''
        ice_obstacles = ''
        grass_obstacles = ''
        for i in range(0, 30):
            stonex = int(random.uniform(coordinates[r[2]][0], coordinates[r[2]][2]))
            stonez = int(random.uniform(coordinates[r[2]][1], coordinates[r[2]][3]))
            stone_obstacles = stone_obstacles + "<DrawBlock x='{}' y='64' z='{}' type='stone' />".format(stonex, stonez)
            stone_obstacles = stone_obstacles + "<DrawBlock x='{}' y='65' z='{}' type='stone' />".format(stonex, stonez)
            cactusx = int(random.uniform(coordinates[r[0]][0], coordinates[r[0]][2]))
            cactusz = int(random.uniform(coordinates[r[0]][1], coordinates[r[0]][3]))
            cactus_obstacles = cactus_obstacles + "<DrawBlock x='{}' y='64' z='{}' type='cactus' />".format(cactusx,
                                                                                                            cactusz)
            cactus_obstacles = cactus_obstacles + "<DrawBlock x='{}' y='65' z='{}' type='cactus' />".format(cactusx,
                                                                                                            cactusz)
            icex = int(random.uniform(coordinates[r[1]][0], coordinates[r[1]][2]))
            icez = int(random.uniform(coordinates[r[1]][1], coordinates[r[1]][3]))
            ice_obstacles = ice_obstacles + "<DrawBlock x='{}' y='64' z='{}' type='ice' />".format(icex, icez)
            ice_obstacles = ice_obstacles + "<DrawBlock x='{}' y='65' z='{}' type='ice' />".format(icex, icez)
            grassx = int(random.uniform(coordinates[r[3]][0], coordinates[r[3]][2]))
            grassz = int(random.uniform(coordinates[r[3]][1], coordinates[r[3]][3]))
            grass_obstacles = grass_obstacles + "<DrawBlock x='{}' y='64' z='{}' type='grass' />".format(grassx, grassz)
            grass_obstacles = grass_obstacles + "<DrawBlock x='{}' y='65' z='{}' type='grass' />".format(grassx, grassz)


        sand_biome_materials = []
        sand_biome_key_list = sorted(list(self.biome_cdfs["sand_biome"].keys()))
        for i in range(coordinates[r[0]][0], coordinates[r[0]][2]):
            for j in range(coordinates[r[0]][1], coordinates[r[0]][3]):
                temp_index = -1
                random_val = random.random()
                while temp_index >= -len(sand_biome_key_list):
                    print("sand biome key list from index:", sand_biome_key_list[temp_index])
                    print("random value:", random_val)
                    if sand_biome_key_list[temp_index] <= random_val:
                        sand_biome_materials.append((i, j, self.biome_cdfs["sand_biome"][sand_biome_key_list[temp_index+1]]))
                        print("added: ", (i, j, self.biome_cdfs["sand_biome"][sand_biome_key_list[temp_index+1]]))
                        break
                        print("test")
                    temp_index -= 1

        snow_biome_materials = []
        snow_biome_key_list = sorted(list(self.biome_cdfs["snow_biome"].keys()))
        for i in range(coordinates[r[1]][0], coordinates[r[1]][2]):
            for j in range(coordinates[r[1]][1], coordinates[r[1]][3]):
                temp_index = -1
                random_val = random.random()
                while temp_index >= -len(snow_biome_key_list):
                    if snow_biome_key_list[temp_index] <= random_val:
                        snow_biome_materials.append((i, j, self.biome_cdfs["snow_biome"][snow_biome_key_list[temp_index+1]]))
                        break
                    temp_index -= 1

        stone_biome_materials = []
        stone_biome_key_list = sorted(list(self.biome_cdfs["stone_biome"].keys()))
        for i in range(coordinates[r[2]][0], coordinates[r[2]][2]):
            for j in range(coordinates[r[2]][1], coordinates[r[2]][3]):
                temp_index = -1
                random_val = random.random()
                while temp_index >= -len(stone_biome_key_list):
                    if stone_biome_key_list[temp_index] <= random_val:
                        stone_biome_materials.append((i, j, self.biome_cdfs["stone_biome"][stone_biome_key_list[temp_index+1]]))
                        break
                    temp_index -= 1

        default_biome_materials = []
        default_biome_key_list = sorted(list(self.biome_cdfs["default_biome"].keys()))
        for i in range(coordinates[r[3]][0], coordinates[r[3]][2]):
            for j in range(coordinates[r[3]][1], coordinates[r[3]][3]):
                temp_index = -1
                random_val = random.random()
                while temp_index >= -len(default_biome_key_list):
                    if default_biome_key_list[temp_index] <= random_val:
                        default_biome_materials.append((i, j, self.biome_cdfs["default_biome"][default_biome_key_list[temp_index+1]]))
                        break
                    temp_index -= 1

        #print(first_biome_materials)
        #print(second_biome_materials)
        #print(third_biome_materials)
        #print(fourth_biome_materials)

        # print(random.uniform(coordinates[r[0]][0],coordinates[r[0]][2]),random.randrange(coordinates[r[0]][1],coordinates[r[0]][3]))
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
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size,
                                                                                                 self.size, self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(self.size, self.size,
                                                                                                 self.size,
                                                                                                 -self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(-self.size, self.size,
                                                                                                 -self.size,
                                                                                                 -self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='64' y2='64' z1='{}' z2='{}' type='fence'/>".format(-self.size, -self.size,
                                                                                                 -self.size,
                                                                                                 self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='63' y2='63' z1='{}' z2='{}' type='planks'/>".format(0, 0, -self.size,
                                                                                                  self.size) + \
               "<DrawLine x1='{}' x2='{}' y1='63' y2='63' z1='{}' z2='{}' type='planks'/>".format(-self.size, self.size,
                                                                                                  0, 0) + \
               "<DrawCuboid x1='{}' x2='{}' y1='63' y2='63' z1='{}' z2='{}' type='sand'/>".format(coordinates[r[0]][0],
                                                                                                  coordinates[r[0]][2],
                                                                                                  coordinates[r[0]][1],
                                                                                                  coordinates[r[0]][
                                                                                                      3]) + \
               "<DrawCuboid x1='{}' x2='{}' y1='63' y2='63' z1='{}' z2='{}' type='snow'/>".format(coordinates[r[1]][0],
                                                                                                  coordinates[r[1]][2],
                                                                                                  coordinates[r[1]][1],
                                                                                                  coordinates[r[1]][
                                                                                                      3]) + \
               "<DrawCuboid x1='{}' x2='{}' y1='63' y2='63' z1='{}' z2='{}' type='stone'/>".format(coordinates[r[2]][0],
                                                                                                   coordinates[r[2]][2],
                                                                                                   coordinates[r[2]][1],
                                                                                                   coordinates[r[2]][
                                                                                                       3]) + \
        ''.join(["<DrawBlock x='{}' y='64' z='{}' type='{}'/>".format(x[0], x[1], x[2]) for x in snow_biome_materials]) + \
        ''.join(["<DrawBlock x='{}' y='64' z='{}' type='{}'/>".format(x[0], x[1], x[2]) for x in sand_biome_materials]) + \
        ''.join(["<DrawBlock x='{}' y='64' z='{}' type='{}'/>".format(x[0], x[1], x[2]) for x in stone_biome_materials]) + \
        ''.join(["<DrawBlock x='{}' y='64' z='{}' type='{}'/>".format(x[0], x[1], x[2]) for x in default_biome_materials]) + \
               stone_obstacles + \
               cactus_obstacles + \
               ice_obstacles + \
               grass_obstacles + \
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
            <ObservationFromFullInventory/>
            <ObservationFromRay/>
            <ObservationFromGrid>
              <Grid name="floorAll">
                <min x="-''' + str(int(self.obs_size)) + '''" y="-1" z="-''' + str(int(self.obs_size)) + '''"/>
                            <max x="''' + str(int(self.obs_size)) + '''" y="0" z="''' + str(int(self.obs_size)) + '''"/>
                          </Grid>
                      </ObservationFromGrid>
                      <SimpleCraftCommands/>
                    </AgentHandlers>
                  </AgentSection>
                </Mission>'''
    def crafting_reqs(self,crafting_list,obs):
        req=[]
        sticks=[]
        planks=[]
        inventory = dict()
        for i in range(0, 9):                           #Checking Inventory
            key = 'InventorySlot_' + str(i) + '_item'
            size = 'InventorySlot_' + str(i) + '_size'
            if key in obs:
                item2 = obs[key]
                quantity = obs[size]
                inventory[item2] = quantity
        for item in crafting_list:
            if item in inventory:   #If we already made it, no need to craft it
                continue
            else:
                req.append(item)   #Still need to craft it
        while(1):
            add=[]
            count=0
            i=0
            for i in req:
                if i in item_recipes.keys():       #Still can be broken down to subcomponents
                    for j in item_recipes[i]:  #For each subcomponent
                        # print(j)
                        for k in range(j[1]):
                            if j[0]!="stick" and j[0]!="planks":
                                add.append(j[0])
                            elif j[0]=="stick":
                                sticks.append(j[0])
                            elif j[0]=="planks":
                                planks.append(j[0])
                    break
                else:
                    count+=1
            if i in item_recipes.keys():   #remove higher level component, replace with subcomponents
                try:
                    req.remove(i)
                except:
                    1
                req=req+(add)
                continue
            if count>=len(req):     #reqs has no more subcomponents, break out of loop
                break
        if sticks.count('stick') > 1:
            x = (sticks.count('stick') - 1) // 4 + 1
            while sticks.count('stick') != x:
                sticks.remove('stick')

        for y in range((len(sticks))):
            planks.append('planks')
            planks.append('planks')

        if planks.count('planks') > 1:
            x = (planks.count('planks') - 1) // 4 + 1
            while planks.count('planks') != x:
                planks.remove('planks')
        log= ["log" for y in range(len(planks))]

        req=req+log
        for i in req:
            if i in inventory:
                for j in range(inventory[i]):
                    req.remove(i)
        for i in req:
            if i=="diamond_ore" or i=="emerald_ore" or i=="redstone_ore" or i=="coal_ore":
                x=req.count(i)
                if i[:-4] not in inventory:
                    continue;
                if x>=inventory[i[:-4]]:
                    for j in range(inventory[i[:-4]]):
                        req.remove(i)
                else:
                    while i in req:
                        req.remove(i)
        return req

    def craft(self, item):
        time.sleep(0.1)
        world_state = Steve.agent_host.getWorldState()
        msg = world_state.observations[-1].text
        obs = json.loads(msg)
        inventory = dict()
        for i in range(0, 9):                           #Checking Inventory
            key = 'InventorySlot_' + str(i) + '_item'
            size = 'InventorySlot_' + str(i) + '_size'
            if key in obs:
                item2 = obs[key]
                quantity = obs[size]
                inventory[item2] = quantity
        if item in item_recipes:
            for j in item_recipes[item]:
                x=j[1]
                if j[0] in inventory:
                    x=j[1]-inventory[j[0]]
                if j[0] == 'stick' or item == 'planks':
                    x=x//4 + (1 if x%4 else 0)
                else:
                    x=x
                print(j[0],x)
                for k in range(x):
                    self.craft(j[0])
        # print(item)
        self.agent_host.sendCommand('craft '+item)

    def crafting_tasks(self,observations):
        if len(self.crafting_list) != 0:
            to_craft=(self.crafting_reqs(self.crafting_list, observations))
        else:
            return []
        return to_craft

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
                # self.craft('iron_pickaxe',observations)
                grid = observations.get(u'floorAll', 0)
                break
        return grid

    def block_action(self, world_state, block_type):
        allow_break_action = False

        if world_state.is_mission_running:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            # print(world_state)
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')

            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                # if len(self.crafting_list) != 0:
                #     # print(self.crafting_list)
                #     for j in self.crafting_list:
                #         self.craft(j, observations)
                #         print("To Craft:", j)

                sight_block = observations['LineOfSight']['type']

                if (sight_block != block_type):
                    self.agent_host.sendCommand('turn 1')

                print(sight_block)
                if (sight_block == block_type):
                    allow_break_action = True
                    self.agent_host.sendCommand('attack 1')
                    self.probability(block_type, world_state)
                    allow_break_action = True

        return allow_break_action

        # self.agent_host.sendCommand('move 1') # move one ahead to make sure you collect

    ## CONSIDERED EDIT: CREATE A LIST/DICT OF "BANNED" BLOCKS, SUCH AS LAVA OR AIR,
    ## THE THE AGENT AVOIDS WHEN LOOKING AT A PATH.
    def probability(self, block_type, world_state):
        if world_state.is_mission_running:
            time.sleep(1)
            world_state = self.agent_host.getWorldState()
            if world_state.number_of_observations_since_last_state > 0:
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                sight_block = observations['LineOfSight']['type']
                print("Looking at: ", sight_block)
                if sight_block == 'sand':
                    if block_type not in self.prob_matrix:
                        self.prob_matrix[block_type] = [1, 0, 0, 0]
                    else:
                        self.prob_matrix[block_type][0] += 1
                if sight_block == 'stone':
                    if block_type not in self.prob_matrix:
                        self.prob_matrix[block_type] = [0, 1, 0, 0]
                    else:
                        self.prob_matrix[block_type][1] += 1
                if sight_block == 'snow':
                    if block_type not in self.prob_matrix:
                        self.prob_matrix[block_type] = [0, 0, 1, 0]
                    else:
                        self.prob_matrix[block_type][2] += 1
                if sight_block == 'grass':
                    if block_type not in self.prob_matrix:
                        self.prob_matrix[block_type] = [0, 0, 0, 1]
                    else:
                        self.prob_matrix[block_type][3] += 1
                print(self.prob_matrix)

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

            if current_space + (self.obs_size * 2 + 1) < len(grid_obs) and \
                    current_best_length[current_space][0] + 1 < \
                    current_best_length[current_space + (self.obs_size * 2 + 1)][0] and \
                    grid_obs[current_space + (self.obs_size * 2 + 1)] != "air" and \
                    current_space != current_best_length[current_space + (self.obs_size * 2 + 1)][1]:
                current_best_length[current_space + (self.obs_size * 2 + 1)] = (
                    current_best_length[current_space][0] + 1, current_space)
                prio_dict[current_space + (self.obs_size * 2 + 1)] = \
                    current_best_length[current_space + (self.obs_size * 2 + 1)][0]

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

            if current_space - (self.obs_size * 2 + 1) >= 0 and \
                    current_best_length[current_space][0] + 1 < \
                    current_best_length[current_space - (self.obs_size * 2 + 1)][
                        0] and \
                    grid_obs[current_space - (self.obs_size * 2 + 1)] != "air" and \
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

    def find_destination(self, grid_obs, destination_block, destination_biome):
        """
        Finds the source and destination block indexes from the list.
        Args
            grid:   <list>  the world grid blocks represented as a list of blocks (see Tutorial.pdf)
        Returns
            start: <int>   source block index in the list
            end:   <int>   destination block index in the list
        """

        ## from Stack overflow: https://stackoverflow.com/questions/398299/looping-in-a-spiral
        def spiral(X, Y, single=True):
            x = y = 0
            dx = 0
            dy = -1
            for i in range(max(X, Y) ** 2):
                if (-X / 2 < x <= X / 2) and (-Y / 2 < y <= Y / 2):
                    # print("location: ", x, y)
                    # print("block at location: ", grid_obs[4*(self.obs_size**2) + self.obs_size * 2 * (y + 50) + x + 50])
                    # print("destination_block: ", destination_block)
                    if single == False:
                        if grid_obs[(((2 * self.obs_size) + 1) ** 2) + (self.obs_size * 2 + 1) * (self.obs_size + y) + self.obs_size + x] in destination_block and\
                        grid_obs[(self.obs_size * 2 + 1) * (self.obs_size + y) + self.obs_size + x] == destination_biome:
                            self.current_block = grid_obs[(((2 * self.obs_size) + 1) ** 2) + (self.obs_size * 2 + 1) * (self.obs_size + y) + self.obs_size + x]
                            return x, y
                    else:
                        if grid_obs[(((2 * self.obs_size) + 1) ** 2) + (self.obs_size * 2 + 1) * (self.obs_size + y) + self.obs_size + x] == destination_block and\
                                grid_obs[(self.obs_size * 2 + 1) * (self.obs_size + y) + self.obs_size + x] == destination_biome:
                            return x, y

                if x == y or (x < 0 and x == -y) or (x > 0 and x == 1 - y):
                    dx, dy = -dy, dx
                x, y = x + dx, y + dy

        if type(destination_block) == list:
            return spiral(2 * self.obs_size, 2 * self.obs_size, False)
        else:
            return spiral(2 * self.obs_size, 2 * self.obs_size)

    def get_shortest_path(self, world_state, destination_block, destination_biome):
        grid = self.load_grid(world_state)

        if (destination_block == "air"):
            destination_index = (self.obs_size * 2 + 1) * (self.obs_size-self.y_pos) + self.obs_size-self.x_pos
            self.true_x_dest = 0
            self.true_y_dest = 0

        else:
            results = self.find_destination(grid, destination_block, destination_biome)
            if results == None:
                self.reverse = True
                return []
                # destination_index = self.obs_size * 2 * (self.y_home + 50) + self.x_home + 50
            else:
                destination_x, destination_y = results[0], results[1]

                destination_index = (self.obs_size * 2 + 1) * (destination_y + self.obs_size) + destination_x + self.obs_size
                self.true_x_dest = self.x_pos + destination_x
                self.true_y_dest = self.y_pos + destination_y

        current_location_index = (self.obs_size * 2 + 1) * self.obs_size + self.obs_size
        # home_index = self.obs_size * 2 * (self.y_home + 50) + self.x_home + 50
        # destination_index = self.obs_size * 2 * (self.y_dest + 50) + self.x_dest + 50

        # shortest_path = self.dijkstra_shortest_path(grid, current_location_index, destination_index)
        aStar_path = aStar.AStar(grid, current_location_index, destination_index, self.obs_size)
        action_list = self.extract_action_list_from_path(aStar_path)

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


item_recipes={'anvil' : [('iron_ingot', 4), ('iron_block', 3)],
'armor_stand' : [('smooth_stone_slab', 1), ('stick', 6)],
'arrow' : [('feather', 1), ('flint', 1), ('stick', 1)],
'baked_potato' : [],
'barrel' : [('planks', 6), ('wooden_slabs', 2)],
'beacon' : [('obsidian', 3), ('nether_star', 1), ('glass', 5)],
'beehive' : [('honeycomb', 3), ('planks', 6)],
'beetroot_soup' : [('beetroot', 6), ('bowl', 1)],
'bone_block' : [('bone_meal', 9)],
'bone_meal' : [('bone', 1)],
'book' : [('leather', 1), ('paper', 3)],
'bookshelf' : [('planks', 6), ('book', 3)],
'bow' : [('string', 3), ('stick', 3)],
'bowl' : [('planks', 3)],
'bread' : [('wheat', 3)],
'brewing_stand' : [('blaze_rod', 1), ('stone_crafting_materials', 3)],
'brick' : [],
'bricks' : [('brick', 4)],
'brick_slab' : [('bricks', 3)],
'brick_stairs' : [('bricks', 6)],
'brick_wall' : [('bricks', 6)],
'bucket' : [('iron_ingot', 3)],
'cake' : [('sugar', 2), ('wheat', 3), ('egg', 1), ('milk_bucket', 3)],
'campfire' : [('coals', 1), ('logs', 3), ('stick', 3)],
'carrot_on_a_stick' : [('fishing_rod', 1), ('carrot', 1)],
'cauldron' : [('iron_ingot', 7)],
'chain' : [('iron_nugget', 2), ('iron_ingot', 1)],
'charcoal' : [],
'chest' : [('planks', 8)],
'chest_minecart' : [('chest', 1), ('minecart', 1)],
'chiseled_nether_bricks' : [('nether_brick_slab', 2)],
'chiseled_polished_blackstone' : [('polished_blackstone_slab', 2)],
'chiseled_quartz_block' : [('quartz_slab', 2)],
'chiseled_red_sandstone' : [('red_sandstone_slab', 2)],
'chiseled_sandstone' : [('sandstone_slab', 2)],
'chiseled_stone_bricks' : [('stone_brick_slab', 2)],
'clay' : [('clay_ball', 4)],
'clock' : [('gold_ingot', 4), ('redstone', 1)],
'coal' : [('coal_ore', 1)],
'coal_block' : [('coal', 9)],
'coarse_dirt' : [('gravel', 2), ('dirt', 2)],
'cobblestone_slab' : [('cobblestone', 3)],
'cobblestone_stairs' : [('cobblestone', 6)],
'cobblestone_wall' : [('cobblestone', 6)],
'comparator' : [('redstone_torch', 3), ('quartz', 1), ('stone', 3)],
'compass' : [('iron_ingot', 4), ('redstone', 1)],
'composter' : [('wooden_slabs', 7)],
'conduit' : [('nautilus_shell', 8), ('heart_of_the_sea', 1)],
'cooked_beef' : [],
'cooked_chicken' : [],
'cooked_cod' : [],
'cooked_mutton' : [],
'cooked_porkchop' : [],
'cooked_rabbit' : [],
'cooked_salmon' : [],
'cookie' : [('wheat', 2), ('cocoa_beans', 1)],
'crafting_table' : [('planks', 4)],
'crossbow' : [('string', 2), ('iron_ingot', 1), ('tripwire_hook', 1), ('stick', 3)],
'cut_red_sandstone' : [('red_sandstone', 4)],
'cut_red_sandstone_slab' : [('cut_red_sandstone', 3)],
'cut_sandstone' : [('sandstone', 4)],
'cut_sandstone_slab' : [('cut_sandstone', 3)],
'daylight_detector' : [('quartz', 3), ('wooden_slabs', 3), ('glass', 3)],
'detector_rail' : [('stone_pressure_plate', 1), ('iron_ingot', 6), ('redstone', 1)],
'diamond' : [('diamond_ore', 1)],
'diamond_axe' : [('diamond', 3), ('stick', 2)],
'diamond_block' : [('diamond', 9)],
'diamond_boots' : [('diamond', 4)],
'diamond_chestplate' : [('diamond', 8)],
'diamond_helmet' : [('diamond', 5)],
'diamond_hoe' : [('diamond', 2), ('stick', 2)],
'diamond_leggings' : [('diamond', 7)],
'diamond_pickaxe' : [('diamond', 3), ('stick', 2)],
'diamond_shovel' : [('diamond', 1), ('stick', 2)],
'diamond_sword' : [('diamond', 2), ('stick', 1)],
'diorite' : [('quartz', 2), ('cobblestone', 2)],
'diorite_slab' : [('diorite', 3)],
'diorite_stairs' : [('diorite', 6)],
'diorite_wall' : [('diorite', 6)],
'dispenser' : [('cobblestone', 7), ('bow', 1), ('redstone', 1)],
'dried_kelp' : [('dried_kelp_block', 1)],
'dried_kelp_block' : [('dried_kelp', 9)],
'dropper' : [('cobblestone', 7), ('redstone', 1)],
'emerald' : [('emerald_block', 1)],
'emerald_block' : [('emerald', 9)],
'enchanting_table' : [('obsidian', 4), ('book', 1), ('diamond', 2)],
'ender_chest' : [('obsidian', 8), ('ender_eye', 1)],
'ender_eye' : [('blaze_powder', 1), ('ender_pearl', 1)],
'end_crystal' : [('glass', 7), ('ghast_tear', 1), ('ender_eye', 1)],
'end_rod' : [('popped_chorus_fruit', 1), ('blaze_rod', 1)],
'end_stone_bricks' : [('end_stone', 4)],
'end_stone_brick_slab' : [('end_stone_bricks', 3)],
'end_stone_brick_stairs' : [('end_stone_bricks', 6)],
'end_stone_brick_wall' : [('end_stone_bricks', 6)],
'fermented_spider_eye' : [('sugar', 1), ('spider_eye', 1), ('brown_mushroom', 1)],
'fire_charge' : [('blaze_powder', 1), ('charcoal', 1), ('gunpowder', 1), ('coal', 1)],
'fishing_rod' : [('string', 2), ('stick', 3)],
'flint_and_steel' : [('flint', 1), ('iron_ingot', 1)],
'flower_pot' : [('brick', 3)],
'furnace' : [('stone_crafting_materials', 8)],
'furnace_minecart' : [('furnace', 1), ('minecart', 1)],
'glass' : [],
'glass_bottle' : [('glass', 3)],
'glass_pane' : [('glass', 6)],
'glistering_melon_slice' : [('gold_nugget', 8), ('melon_slice', 1)],
'glowstone' : [('glowstone_dust', 4)],
'golden_apple' : [('gold_ingot', 8), ('apple', 1)],
'golden_axe' : [('gold_ingot', 3), ('stick', 2)],
'golden_boots' : [('gold_ingot', 4)],
'golden_carrot' : [('gold_nugget', 8), ('carrot', 1)],
'golden_chestplate' : [('gold_ingot', 8)],
'golden_helmet' : [('gold_ingot', 5)],
'golden_hoe' : [('gold_ingot', 2), ('stick', 2)],
'golden_leggings' : [('gold_ingot', 7)],
'golden_pickaxe' : [('gold_ingot', 3), ('stick', 2)],
'golden_shovel' : [('gold_ingot', 1), ('stick', 2)],
'golden_sword' : [('gold_ingot', 2), ('stick', 1)],
'gold_block' : [('gold_ingot', 9)],
'gold_ingot' : [('gold_ore',1),('coal',1)],
'gold_nugget' : [('gold_ingot', 1)],
'grindstone' : [('planks', 2), ('stone_slab', 1), ('stick', 2)],
'hay_block' : [('wheat', 9)],
'heavy_weighted_pressure_plate' : [('iron_ingot', 2)],
'honeycomb_block' : [('honeycomb', 4)],
'honey_block' : [('honey_bottle', 4)],
'honey_bottle' : [('glass_bottle', 4), ('honey_block', 1)],
'hopper' : [('chest', 1), ('iron_ingot', 5)],
'hopper_minecart' : [('minecart', 1), ('hopper', 1)],
'iron_axe' : [('iron_ingot', 3), ('stick', 2)],
'iron_bars' : [('iron_ingot', 6)],
'iron_block' : [('iron_ingot', 9)],
'iron_boots' : [('iron_ingot', 4)],
'iron_chestplate' : [('iron_ingot', 8)],
'iron_door' : [('iron_ingot', 6)],
'iron_helmet' : [('iron_ingot', 5)],
'iron_hoe' : [('iron_ingot', 2), ('stick', 2)],
'iron_ingot' : [('iron_ore',1),('coal',1)],
'iron_leggings' : [('iron_ingot', 7)],
'iron_nugget' : [('iron_ingot', 1)],
'iron_pickaxe' : [('iron_ingot', 3), ('stick', 2)],
'iron_shovel' : [('iron_ingot', 1), ('stick', 2)],
'iron_sword' : [('iron_ingot', 2), ('stick', 1)],
'iron_trapdoor' : [('iron_ingot', 4)],
'item_frame' : [('leather', 1), ('stick', 8)],
'jack_o_lantern' : [('carved_pumpkin', 1), ('torch', 1)],
'jukebox' : [('planks', 8), ('diamond', 1)],
'ladder' : [('stick', 7)],
'lantern' : [('iron_nugget', 8), ('torch', 1)],
'lapis_block' : [('lapis_lazuli', 9)],
'lapis_lazuli' : [],
'lead' : [('slime_ball', 1), ('string', 4)],
'leather' : [('rabbit_hide', 4)],
'leather_boots' : [('leather', 4)],
'leather_chestplate' : [('leather', 8)],
'leather_helmet' : [('leather', 5)],
'leather_horse_armor' : [('leather', 7)],
'leather_leggings' : [('leather', 7)],
'lectern' : [('wooden_slabs', 4), ('bookshelf', 1)],
'lever' : [('cobblestone', 1), ('stick', 1)],
'light_weighted_pressure_plate' : [('gold_ingot', 2)],
'lodestone' : [('netherite_ingot', 1), ('chiseled_stone_bricks', 8)],
'loom' : [('planks', 2), ('string', 2)],
'magma_block' : [('magma_cream', 4)],
'magma_cream' : [('blaze_powder', 1), ('slime_ball', 1)],
'map' : [('compass', 1), ('paper', 8)],
'melon' : [('melon_slice', 9)],
'melon_seeds' : [('melon_slice', 1)],
'minecart' : [('iron_ingot', 5)],
'mojang_banner_pattern' : [('enchanted_golden_apple', 1), ('paper', 1)],
'mossy_cobblestone' : [('vine', 1), ('cobblestone', 1)],
'mossy_cobblestone_slab' : [('mossy_cobblestone', 3)],
'mossy_cobblestone_stairs' : [('mossy_cobblestone', 6)],
'mossy_cobblestone_wall' : [('mossy_cobblestone', 6)],
'mossy_stone_bricks' : [('stone_bricks', 1), ('vine', 1)],
'mossy_stone_brick_slab' : [('mossy_stone_bricks', 3)],
'mossy_stone_brick_stairs' : [('mossy_stone_bricks', 6)],
'mossy_stone_brick_wall' : [('mossy_stone_bricks', 6)],
'mushroom_stew' : [('red_mushroom', 1), ('brown_mushroom', 1), ('bowl', 1)],
'nether_brick' : [],
'nether_bricks' : [('nether_brick', 4)],
'nether_brick_fence' : [('nether_bricks', 4), ('nether_brick', 2)],
'nether_brick_slab' : [('nether_bricks', 3)],
'nether_brick_stairs' : [('nether_bricks', 6)],
'nether_brick_wall' : [('nether_bricks', 6)],
'nether_wart_block' : [('nether_wart', 9)],
'note_block' : [('planks', 8), ('redstone', 1)],
'packed_ice' : [('ice', 9)],
'painting' : [('wool', 1), ('stick', 8)],
'paper' : [('sugar_cane', 3)],
'piston' : [('planks', 3), ('cobblestone', 4), ('iron_ingot', 1), ('redstone', 1)],
'planks' : [('log', 1)],
'redstone' : [('redstone_ore',1)],
'redstone_torch' : [('redstone',1),('stick',1)],
'stick' : [('planks', 2)],
'stone_pickaxe' : [('cobblestone', 3), ('stick', 2)],
}


if __name__ == '__main__':
    print("Starting...")
    Steve = SteverCrafter()
    world_state = Steve.init_malmo()

    if world_state.is_mission_running:
        time.sleep(0.5)
        world_state = Steve.agent_host.getWorldState()
        while world_state.number_of_observations_since_last_state <= 0:
            time.sleep(0.5)

        if world_state.number_of_observations_since_last_state > 0:
            msg = world_state.observations[-1].text
            observations = json.loads(msg)
            ##### EDITING THIS INTO THE PATHFINDING:

            list_of_blocks=Steve.crafting_tasks(observations)
            #block = list_of_blocks[0]
            block = list_of_blocks

    count=0

    action_index = 0
    ## At this point, we'll need to have determined what our destination is.
    ## Air is the default that will just send it to the default destination,
    ## but if a block is generated in the world and that type is specified,
    ## can use that instead and it will get the path to that block
    biome_ranks = {"sand_biome": 0,
                   "snow_biome": 0,
                   "stone_biome": 0,
                   "default_biome": 0}

    for material in block:
        for biome in Steve.biome_probabilities:
            if material in Steve.biome_probabilities[biome] and Steve.biome_probabilities[biome][material]*(Steve.size**2) > 10:
                biome_ranks[biome] += 1

    biome_to_floor = {"sand_biome": "sand",
                   "snow_biome": "snow",
                   "stone_biome": "stone",
                   "default_biome": "grass"}

    Steve.biome_dest = biome_to_floor[max(biome_ranks, key=biome_ranks.get)]
    print(Steve.biome_dest)


    action_list = Steve.get_shortest_path(world_state, block, Steve.biome_dest)
    # print(action_list)
    temp = 1

    while world_state.is_mission_running:
        # sys.stdout.write(".")
        time.sleep(0.1)
        print("Finding Block: ", Steve.current_block)

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
            # print("Found block")
            allow_break = Steve.block_action(world_state, Steve.current_block)
            #allow_break = Steve.block_action(world_state, block)
            if allow_break == True:

                if len(action_list) == action_index:
                    # Need to wait few seconds to let the world state realise I'm in end block.
                    # Another option could be just to add no move actions -- I thought sleep is more elegant.
                    time.sleep(2)
                time.sleep(0.1)
                world_state = Steve.agent_host.getWorldState()
                time.sleep(0.1)
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                list_of_blocks = Steve.crafting_tasks(observations)
                print(list_of_blocks)
                count += 1
                if len(list_of_blocks) == 0:
                    for i in Steve.crafting_list:
                        print("Crafting", i)
                        Steve.craft(i)
                        Steve.reverse = True
                        Steve.current_block = "air"
                    #break
                elif block != list_of_blocks[0] or count > 3:
                    count = 0
                    block = list_of_blocks
                    #block = list_of_blocks[0]
                    action_list = Steve.get_shortest_path(world_state, block, Steve.biome_dest)

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
            # if (len(needed) > 0 and allow_break == True):
            #     block = needed.pop()

            action_index = 0
            #### BREAK POINT 1 #####
            ## From here, we would use the probabilities to pick a biome.
            ## Once we pick a biome, we then use shortest path to
            if Steve.reverse == False and Steve.current_block != "air":
                action_list = Steve.get_shortest_path(world_state, block, Steve.biome_dest)
                ########################


                # print("Finding new block: ", action_list)
                time.sleep(1)

            ## if there are no diamond ore in the observation view, Steve.reverse will be
            ## set to true, and action_list will be empty
            if Steve.reverse == True:
                Steve.biome_dest = "plank"
                action_list = Steve.get_shortest_path(world_state, "air", Steve.biome_dest)

        else:
            # Sending the next commend from the action list -- found using the Dijkstra algo.
            if action_index >= len(action_list):
                print("Error:", "out of actions, but mission has not ended!")


                time.sleep(1)
                action_index = -1
                if Steve.current_block != "air":
                    action_list = Steve.get_shortest_path(world_state, block, Steve.biome_dest)
                else:
                    action_list = Steve.get_shortest_path(world_state, "air", "plank")

                print("reverse:", Steve.reverse)
                print("action_list", action_list)
                print("current block", Steve.current_block)

                if len(action_list) != 0:
                    print("There is another")
                    Steve.reverse = False

            else:

                ## We may want code that deals with any obstacles in the agent's way as well,
                ## Since it's possible that the return path gets blocked
                ## I also want to update the dijkstra's algorithm to avoid obstacles, but that's getting
                ## too invested in Dijkstra's when we will be replacing it with a search eventually.

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

                Steve.agent_host.sendCommand(action_list[action_index])

            action_index += 1

            if len(action_list) == action_index:
                # Need to wait few seconds to let the world state realise I'm in end block.
                # Another option could be just to add no move actions -- I thought sleep is more elegant.
                time.sleep(2)

            world_state = Steve.agent_host.getWorldState()

            for error in world_state.errors:
                print("Error:", error.text)