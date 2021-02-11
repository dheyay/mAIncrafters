# Rllib docs: https://docs.ray.io/en/latest/rllib.html

##Crafting Base Code, Using assignment two and craft_work.py as a starting point
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


class DiamondCollector(gym.Env):

    def __init__(self, env_config):  
        # Static Parameters
        self.size = 50
        self.reward_density = .1
        self.penalty_density = .02
        self.obs_size = 5
        self.max_episode_steps = 100
        self.log_frequency = 1
        self.action_dict = {
            0: 'move 1',  # Move one block forward
            1: 'turn 1',  # Turn 90 degrees to the right
            2: 'turn -1',  # Turn 90 degrees to the left
            3: 'attack 1'  # Destroy block
        }

        # Rllib Parameters

        self.action_space = Discrete(len(self.action_dict))
        # self.action_space = gym.spaces.Box(low=np.array([-1,-1,0]),high=np.array([1,1,1]),dtype=np.float32)
        self.observation_space = Box(0, 1, shape=(2 * self.obs_size * self.obs_size, ), dtype=np.float32)

        # Malmo Parameters
        self.agent_host = MalmoPython.AgentHost()
        try:
            self.agent_host.parse( sys.argv )
        except RuntimeError as e:
            print('ERROR:', e)
            print(self.agent_host.getUsage())
            exit(1)

        # DiamondCollector Parameters
        self.obs = None
        self.allow_break_action = False
        self.episode_step = 0
        self.episode_return = 0
        self.returns = []
        self.steps = []

    def reset(self):
        """
        Resets the environment for the next episode.

        Returns
            observation: <np.array> flattened initial obseravtion
        """
        print("Next Episode \n")
        # Reset Malmo
        world_state = self.init_malmo()

        # Reset Variables
        self.returns.append(self.episode_return)
        current_step = self.steps[-1] if len(self.steps) > 0 else 0
        self.steps.append(current_step + self.episode_step)
        self.episode_return = 0
        self.episode_step = 0

        # Log
        if len(self.returns) > self.log_frequency + 1 and \
            len(self.returns) % self.log_frequency == 0:
            self.log_returns()

        # Get Observation
        self.obs, self.allow_break_action = self.get_observation(world_state)

        return self.obs

    def step(self, action):
        """
        Take an action in the environment and return the results.

        Args
            action: <int> index of the action to take

        Returns
            observation: <np.array> flattened array of obseravtion
            reward: <int> reward from taking action
            done: <bool> indicates terminal state
            info: <dict> dictionary of extra information
        """

        # Get Action
        # command=action
        # if command[2]>0.5:
        #     self.agent_host.sendCommand("attack "+str(1))
        #     self.agent_host.sendCommand("turn 0")
        #     self.agent_host.sendCommand("move 0")
        #     time.sleep(0.5)
        # else:
        #     self.agent_host.sendCommand("attack "+str(0))
        #     self.agent_host.sendCommand("turn "+str(command[0]))
        #     self.agent_host.sendCommand("move "+str(command[1]))
        #     time.sleep(.2)
        # self.episode_step += 1
        command = self.action_dict[action]
        if command != 'attack 1' or self.allow_break_action:
            self.agent_host.sendCommand(command)
            time.sleep(.2)
            self.episode_step += 1

        # Get Observation
        world_state = self.agent_host.getWorldState()
        for error in world_state.errors:
            print("Error:", error.text)
        self.obs, self.allow_break_action = self.get_observation(world_state) 

        # Get Done
        done = not world_state.is_mission_running 

        # Get Reward
        reward = 0
        for r in world_state.rewards:
            reward += r.getValue()
        self.episode_return += reward

        return self.obs, reward, done, dict()

    def get_mission_xml(self):
        x = np.random.randint(low=-25,high=25, size=250)
        z = np.random.randint(low=-25,high=25, size=250)
        xml_test=""
        for i in range(0, 250):
            xml="<DrawBlock x='{}' y='{}' z='{}' type='log' />\n"
            xml_test=xml_test+xml.format(str(x[i]),'2',str(z[i]))
        x2 =np.random.randint(low=-25,high=25, size=50)
        z2 = np.random.randint(low=-25,high=25, size=50)
        xml_test2=""
        for i in range(0, 50):
            xml2="<DrawBlock x='{}' y='{}' z='{}' type='lava' />\n"
            xml_test2=xml_test2+xml2.format(str(x2[i]),'1',str(z2[i]))
        return '''<?xml version="1.0" encoding="UTF-8" standalone="no" ?>
                <Mission xmlns="http://ProjectMalmo.microsoft.com" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">

                    <About>
                        <Summary>Diamond Collector</Summary>
                    </About>

                    <ServerSection>
                        <ServerInitialConditions>
                            <Time>
                                <StartTime>12000</StartTime>
                                <AllowPassageOfTime>false</AllowPassageOfTime>
                            </Time>
                            <Weather>clear</Weather>
                        </ServerInitialConditions>
                        <ServerHandlers>
                            <FlatWorldGenerator generatorString="3;7,2;1;"/>
                            <DrawingDecorator>''' + \
                                "<DrawCuboid x1='{}' x2='{}' y1='2' y2='2' z1='{}' z2='{}' type='air'/>".format(-self.size, self.size, -self.size, self.size) + \
                                "<DrawCuboid x1='{}' x2='{}' y1='1' y2='1' z1='{}' z2='{}' type='grass'/>".format(-self.size, self.size, -self.size, self.size) + \
                                    xml_test + \
                                    xml_test2 + \
                                '''<DrawBlock x='0'  y='2' z='0' type='air' />
                                <DrawBlock x='0'  y='1' z='0' type='grass' />
                            </DrawingDecorator>
                            <ServerQuitWhenAnyAgentFinishes/>
                        </ServerHandlers>
                    </ServerSection>

                    <AgentSection mode="Survival">
                        <Name>CS175DiamondCollector</Name>
                        <AgentStart>
                            <Placement x="0.5" y="2" z="0.5" pitch="45" yaw="0"/>
                            <Inventory>
                                <InventoryItem slot="0" type="diamond_axe"/>
                                <InventoryItem slot="1" type="cobblestone" quantity="64"/>
                            </Inventory>
                        </AgentStart>
                        <AgentHandlers>
                            <RewardForCollectingItem>
                                <Item type="log" reward="1000" />
                            </RewardForCollectingItem>
                            <RewardForTouchingBlockType>
                                <Block type="lava" reward="-100" />
                            </RewardForTouchingBlockType>
                            <DiscreteMovementCommands/>
                            <ObservationFromFullStats/>
                            <ObservationFromRay/>
                            <ObservationFromGrid>
                                <Grid name="floorAll">
                                    <min x="-'''+str(int(self.obs_size/2))+'''" y="-1" z="-'''+str(int(self.obs_size/2))+'''"/>
                                    <max x="'''+str(int(self.obs_size/2))+'''" y="0" z="'''+str(int(self.obs_size/2))+'''"/>
                                </Grid>
                            </ObservationFromGrid>
                            <ObservationFromFullInventory/>
                            <InventoryCommands/>
                            <AgentQuitFromReachingCommandQuota total="'''+str(300*self.max_episode_steps)+'''" />
                            <AgentQuitFromTouchingBlockType>
                                <Block type="bedrock" />
                            </AgentQuitFromTouchingBlockType>
                            <SimpleCraftCommands/>
                        </AgentHandlers>
                    </AgentSection>
                </Mission>'''

    def checkInventoryForItem(self, obs, requested):
        for i in range(0, 39):
            key = 'InventorySlot_' + str(i) + '_item'
            if key in obs:
                item = obs[key]
                if item == requested:
                    return True
        return False

    def init_malmo(self):
        """
        Initialize new malmo mission.
        """
        my_mission = MalmoPython.MissionSpec(self.get_mission_xml(), True)
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

    def get_observation(self, world_state):
        """
        Use the agent observation API to get a flattened 2 x 5 x 5 grid around the agent. 
        The agent is in the center square facing up.

        Args
            world_state: <object> current agent world state

        Returns
            observation: <np.array> the state observation
            allow_break_action: <bool> whether the agent is facing a diamond
        """
        obs = np.zeros((2 * self.obs_size * self.obs_size, ))
        allow_break_action = False

        while world_state.is_mission_running:
            time.sleep(0.1)
            world_state = self.agent_host.getWorldState()
            if len(world_state.errors) > 0:
                raise AssertionError('Could not load grid.')

            if world_state.number_of_observations_since_last_state > 0:
                # First we get the json from the observation API
                msg = world_state.observations[-1].text
                observations = json.loads(msg)
                self.craft('stone_pickaxe',observations)
                # Get observation
                grid = observations['floorAll']
                for i, x in enumerate(grid):
                    obs[i] = x == 'log' or x == 'lava'

                # Rotate observation with orientation of agent
                obs = obs.reshape((2, self.obs_size, self.obs_size))
                yaw = observations['Yaw']
                if yaw >= 225 and yaw < 315:
                    obs = np.rot90(obs, k=1, axes=(1, 2))
                elif yaw >= 315 or yaw < 45:
                    obs = np.rot90(obs, k=2, axes=(1, 2))
                elif yaw >= 45 and yaw < 135:
                    obs = np.rot90(obs, k=3, axes=(1, 2))
                obs = obs.flatten()

                allow_break_action = observations['LineOfSight']['type'] == 'log'
                
                break

        return obs, allow_break_action

    def craft(self,item,obs):
        inventory=dict()
        for i in range(0, 9):
            key = 'InventorySlot_' + str(i) + '_item'
            size = 'InventorySlot_' + str(i) + '_size'
            if key in obs:
                item2 = obs[key]
                quantity = obs[size]
                inventory[item2]=quantity
        for i in item_recipes[item]:
            try:
                count=inventory[i[0]]
            except:
                count=0
            for k in range(int(i[1])-count):
                self.craft(i[0],obs)
                self.agent_host.sendCommand('craft '+i[0])
        self.agent_host.sendCommand('craft ' + item)

    def log_returns(self):
        """
        Log the current returns as a graph and text file

        Args:
            steps (list): list of global steps after each episode
            returns (list): list of total return of each episode
        """
        box = np.ones(self.log_frequency) / self.log_frequency
        returns_smooth = np.convolve(self.returns[1:], box, mode='same')
        plt.clf()
        plt.plot(self.steps[1:], returns_smooth)
        plt.title('Diamond Collector')
        plt.ylabel('Return')
        plt.xlabel('Steps')
        plt.savefig('returns.png')

        with open('returns.txt', 'w') as f:
            for step, value in zip(self.steps[1:], self.returns[1:]):
                f.write("{}\t{}\n".format(step, value)) 
item_recipes={'stone_pickaxe':[('cobblestone',3),('stick',2)],'stick':[('planks',2)],'planks':[('log',1)],'log':[],'cobblestone':[]}


if __name__ == '__main__':
    ray.init()
    trainer = ppo.PPOTrainer(env=DiamondCollector, config={
        'env_config': {},           # No environment parameters to configure
        'framework': 'torch',       # Use pyotrch instead of tensorflow
        'num_gpus': 0,              # We aren't using GPUs
        'num_workers': 0            # We aren't using parallelism
    })

    while True:
        print(trainer.train())


