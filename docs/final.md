---
layout: default
title: Final Report
---

## Project Summary
Suppose you are playing Minecraft and as a regular miner in a world, you want to start a large building project but are not sure about everything you need for it. That is where our mAinCrafter comes in. Our agent focuses on automation of menial tasks in Minecraft to make the gameplay more streamlined and less repetitive for the player. The agent does the finding and mining so you can focus on desigining your latest masterpiece.

ADD IMAGE HERE

The main goal of this project is to allow the user to give the agent items to craft and the agent will automatically move around and seek out the materials needed to craft it and acquire them. The agent will take into account the placing of the elements and if the item needed to be crafted has a sub-element that also needs crafting, it will find all the base elements needed and provide the user with the final element after crafting it. The agent will be able to find the elements in a large/complex map while avoiding obstacles and being efficient about time as well. It can also be used in order to gather materials stated by the user. 
For example, before building a castle, the user can simply instruct the agent to gather wood or cobblestone.

#### ADD VIDEO 

## Approaches
Our approach to the problem is divided into multiple parts with each part having a unique problem for the agent to tackle.

### Baseline

##### Locating
For locating objects, the current version of the agent uses a spiral search though the observation level that is in the same plane as the agent (at this point in time, the agent has an observation grid equivalent in size to the world). The way it works is to iterate in a direction along the grid until it hits a "corner" spcace in the grid, then changes direction ([Source: StackOverflow](https://stackoverflow.com/questions/398299/looping-in-a-spiral)). This allows us to find the closest location with a material of interest, at which point the agent determines the shortest path there (using Dijkstra's algorithm), then goes to collect the material. After this material is collected, this is repeated, checking for the closest material to the current location. If nothing is found nearby, it currently returns to the starting point, and effectively restarts the search from there. This allows the agent to avoid missing any blocks that end up outside of the observation window after moving in a given direction.


As the basic functions of the agent are confirmed and solidified, the observation window will be reduced to better mimic a player's view. As a result of this restriction, it will be entirely possible that no desired materials are observable from the starting point of the agent, and this is where the AI will come into play. More details will be in the Remaining Goals and Challenges section, but the short version is that we will be training the agent to associate various world characteristics and landscapes with materials, and have the agent move towards regions that are likely to contain the object in its searches.


##### Navigating
Dijkstra's shortest path Algorithm was used as our method of navigation for the baseline once we have determined the location of the object we are looking for. We used Dijkstra's algorithm to find the path between the agent's current location and some material location in two dimensions, while we have a stack implemented to keep record of the current shortest path back. As the environment got more complex, Dijkstra's was also be used to find the return path from the agent's current location to the starting position in coordination with the general path from the stack (since the farther we go, we will eventually be out of observation range of the starting point).


Dijkstra's shortest path for the agent: 
The way we are using Dijkstra's Algorithm in our baseline is as follows:
- set the starting location and destination, and have a current space used to keep track of position, which starts at the starting location
  - the cost to travel to the starting location is 0, and the cost for every other space defaults to infinity
- iterate over the spaces that are adjacent to the current space
  - if the cost of travelling to that space is greater than 1 + the cost to the current space, then the next space's cost is set to (1 + cost of current space), and its previous space is set to the current space.
- this repeats, updating the current space as it calculates, and finally results in a mapping of (space_loaction) -> (cost, previous_space) for all relevant spaces
- starting from the destination space, we then get the path by recording the the previous spaces of each space in the path until we reach the starting location
- finally, the actions necessary for the agent to travel that path are extracted


Once the path is found and the agent moves to the location, the material in question is collected (if the material is a block, the agent breaks the block, then collects), and the location algorithm then Dijkstra's Algorithm are run in succession repeatedly until no nearby blocks are found, at which point the agent returns to the starting position. In the gif below, the basic approach for a dijkstra's shortest path algorithm is shown, when using this to find the shortest path, the agent looks at every block in all directions until the target block is seen. Then the shortest path is calculated.


![Dijkstras_progress_animation](https://user-images.githubusercontent.com/43485198/107836543-6853cb80-6d52-11eb-81de-d6ad897d4cd8.gif)

[Source: WikiPedia](https://en.wikipedia.org/wiki/File:Dijkstras_progress_animation.gif)



##### Recipe Formulation and Crafting
Malmo provides functions to craft items. However, there is no feature that examines recipes for the materials required. To do so, we found the files provided by Minecraft itself, and found the base code. By developing a file analysis code, we were able to open and extract the recipe from each of the files (1 for each craftable item). Once we got the information, we placed it into one large dictionary in python, with each variable name as the key and the recipe as the value (a list with a tuple containing the material name and quantity for each ingredient). 

Using information we learned from the Malmo examples, we then find a way to actually craft the items. The function begins with analyzing the inventory, to see what materials we already have. Once we know this, we examine the recipe by checking the dictionary, and for each item required, we check the quantity required and subtract the amount we have in the inventory. Then we recursively call the craft function until we reach an item that is not in the recipe dictionary (therefore cannot be crafted and must be found in the game, like logs, or cobblestone). The agent must find these items. From there, we begin to craft each component, sometimes having to go through many iterations of crafting until we reach the intended item. For example: if we send the craft function for a stone pickaxe, it would recursively search for 3 cobblestone, and for 2 sticks. If they are not in the inventory, it would send the agent to look for cobblestone, and for a log since the log is used for planks which is how you make sticks which is how you make the pickaxe)

Source: [Malmo By Microsoft](https://github.com/microsoft/malmo)

### Proposed Approach

##### Locationg
add for new agent

##### Navigation
A* - add psuedo - hueristic equation

##### Crafting
add for new agent

## Evaluation
#### Metrics:
Time spent on task: The time spent should be minimized. The AI can be considered successful if it approaches or is better than the time spent by an average human on the same task.  

#### Distance travelled: 
The amount of distance traveled by the agent should also be minimized. This can be compared to the amount of distance traveled by a human player who has not plotted out their exact path, unlike the AI.

#### Accuracy: 
The measure of how close the AI is to completing the task. If all necessary materials are not available, it will be judged on how close it was to accomplishing the task, i.e. finishing all the other subtasks.  

#### Baseline:
The baseline for both metrics will be the time and distance spent by an average user. If the AI is within 150% the standard baseline, it can be regarded as successful. 
