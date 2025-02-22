---
layout: default
title: Status
youtubeId: 5goJvONQvdg
---

## Project Summary
For our project in Minecraft AI, we will be focusing on navigation and automation of menial tasks in Minecraft in order to make the game more streamlined and less repetitive. The main goal of this project is to allow the agent to be given a user crafting recipe, and the agent will automatically move around and seek out the materials needed to craft it and gather them accordingly. For a more improved version of the agent, a more complex map with obstacles/natural elements specific to the terrain will be used as the agent will have to not only navigate to the resources but also avoid different obstacles and natural structures in the way while also being efficient about time.  It can also be used in order to just gather materials defined by the user. For example, before a large building project, the user can simply tell it to collect wood or cobblestone, and start the AI.

#### Take a look at our Project Video below
{% include youtubePlayer.html id=page.youtubeId %}
{% comment %} 
    [![Image_presentation](https://user-images.githubusercontent.com/43485198/107839513-4c0b5b00-6d61-11eb-8c12-af1234b17ddc.png)](https://youtu.be/5goJvONQvdg)
{% endcomment %}



## Approach
Our approach to the problem is divided into multiple parts with each part having a unique problem for the agent to tackle.

#### Locating
For locating objects, the current version of the agent uses a spiral search though the observation level that is in the same plane as the agent (at this point in time, the agent has an observation grid equivalent in size to the world). The way it works is to iterate in a direction along the grid until it hits a "corner" spcace in the grid, then changes direction ([Source: StackOverflow](https://stackoverflow.com/questions/398299/looping-in-a-spiral)). This allows us to find the closest location with a material of interest, at which point the agent determines the shortest path there (using Dijkstra's algorithm), then goes to collect the material. After this material is collected, this is repeated, checking for the closest material to the current location. If nothing is found nearby, it currently returns to the starting point, and effectively restarts the search from there. This allows the agent to avoid missing any blocks that end up outside of the observation window after moving in a given direction.


As the basic functions of the agent are confirmed and solidified, the observation window will be reduced to better mimic a player's view. As a result of this restriction, it will be entirely possible that no desired materials are observable from the starting point of the agent, and this is where the AI will come into play. More details will be in the Remaining Goals and Challenges section, but the short version is that we will be training the agent to associate various world characteristics and landscapes with materials, and have the agent move towards regions that are likely to contain the object in its searches.


#### Navigating
Dijkstra's shortest path Algorithm is currently used as our method of navigation once we have determined the location of the object we are looking for. As it stands currently, we use Dijkstra's algorithm to find the path between the agent's current location and some material location in two dimensions, while we have a stack implemented to keep reccord of the current shortest path back. As the environment get more complex, Dijkstra's will also be used to find the return path from the agent's current location to the starting position in coordination with the general path from the stack (since the farther we go, we will eventually be out of observation range of the starting point).


Dijkstra's shortest path for the agent: 
The way we are using Dijkstra's Algorithm in are project is as follows:
- set the starting location and destination, and have a current space used to keep track of position, which starts at the starting location
  - the cost to travel to the starting location is 0, and the cost for every other space defaults to infinity
- iterate over the spaces that are adjacent to the current space
  - if the cost of travelling to that space is greater than 1 + the cost to the current space, then the next space's cost is set to (1 + cost of current space), and its previous space is set to the current space.
- this repeats, updating the current space as it calculates, and finally results in a mapping of (space_loaction) -> (cost, previous_space) for all relevant spaces
- starting from the destination space, we then get the path by recording the the previous spaces of each space in the path until we reach the starting location
- finally, the actions necessary for the agent to travel that path are extracted


In the current version of the agent, once the path is found and the agent moves to the location, the material in question is collected (if the material is a block, the agent breaks the block, then collects), and the location algorithm then Dijkstra's Algorithm are run in succession repeatedly until no nearby blocks are found, at which point the agent returns to the starting position.


In the gif below, there is a visualization of Dijkstra's algorithm being used to find a path while an obstacle is in the way. This will be quite relevant to our agent, since when generating paths, there will be choices to either consider a block as an obstacle blocking us or something that is climbable (for a 3D implementation of Dijkstra's Algorithm), and even if climbable, if there is still a route to the destination beyond it.

![Dijkstras_progress_animation](https://user-images.githubusercontent.com/43485198/107836543-6853cb80-6d52-11eb-81de-d6ad897d4cd8.gif)

[Source: WikiPedia](https://en.wikipedia.org/wiki/File:Dijkstras_progress_animation.gif)


#### Recipe Formulation and Crafting
Malmo provides functions to craft items. However, there is no feature that examines recipes for the materials required. To do so, we found the files provided by Minecraft itself, and found the base code. By developing a file analysis code, we were able to open and extract the recipe from each of the files (1 for each craftable item). Once we got the information, we placed it into one large dictionary in python, with each variable name as the key and the recipe as the value (a list with a tuple containing the material name and quantity for each ingredient). 

Using information we learned from the Malmo examples, we then find a way to actually craft the items. The function begins with analyzing the inventory, to see what materials we already have. Once we know this, we examine the recipe by checking the dictionary, and for each item required, we check the quantity required and subtract the amount we have in the inventory. Then we recursively call the craft function until we reach an item that is not in the recipe dictionary (therefore cannot be crafted and must be found in the game, like logs, or cobblestone). The agent must find these items. From there, we begin to craft each component, sometimes having to go through many iterations of crafting until we reach the intended item. For example: if we send the craft function for a stone pickaxe, it would recursively search for 3 cobblestone, and for 2 sticks. If they are not in the inventory, it would send the agent to look for cobblestone, and for a log since the log is used for planks which is how you make sticks which is how you make the pickaxe)

Source: [Malmo By Microsoft](https://github.com/microsoft/malmo)

## Evaluation
#### Metrics:
Time spent on task: The time spent should be minimized. The AI can be considered successful if it approaches or is better than the time spent by an average human on the same task.  

#### Distance travelled: 
The amount of distance traveled by the agent should also be minimized. This can be compared to the amount of distance traveled by a human player who has not plotted out their exact path, unlike the AI.

#### Accuracy: 
The measure of how close the AI is to completing the task. If all necessary materials are not available, it will be judged on how close it was to accomplishing the task, i.e. finishing all the other subtasks.  

#### Baseline:
The baseline for both metrics will be the time and distance spent by an average user. If the AI is within 150% the standard baseline, it can be regarded as successful. 


## Remaining Goals and Challenges:
The main goal that remains is to improve the pathfinding algorithm and compare results to see which is the best performing algorithm with time being the evaluating factor. We are currently planning on using A* in addition to the spiral search detailed above, as well as using some sort of learning algorithm to determine and update the weights (examples and current candidates include a bayesian or markov model to represent the probabilities or likelihoods of various materials given an environment). The A* algorithm is similar to Dijkstra's Algorithm, except rather than only having a destination with the goal of minimum cost, we can use a heuristic function to take probabilities or likelihoods from, say, a markov model, and use the inverse probabilities of material presence as a cost. In this way, as long as we have a proper heuristic function, we can (relatively) quickly find prospective areas to travel to based on their learned material content. 

The gif below is in the same situation and style of that of the Dijkstra's Algorithm one above, but shows A* instead. The situation shown is not quite how we will be using it; we won't be looking for the best path to a single location, but instead we have some "idealized" location, and we want to find which of the paths has the closest relation to the end state (if not the end state itself). An example might be that the agent believes that a grassy area often borders a stone area, which in turn tends to border a desert area. Say additionally that the agent "knows" that logs are only found in a desert area. Then when we run A* with the intent to find logs, we are effectively searching for a desert environment. If the area we start in is all diamond ore, and there are bordering areas of grass and stone on either side, the agent would not find desert directly, but would guess that since stone often accompanies desert, whereas grass may accomany stone which may lead to desert, the best bet for closest results is to travel to the stone area. This is a large generalization, but that's the idea.

![Astar_progress_animation](https://upload.wikimedia.org/wikipedia/commons/5/5d/Astar_progress_animation.gif)

[Source: WikiPedia](https://en.wikipedia.org/wiki/A*_search_algorithm#/media/File:Astar_progress_animation.gif)

Regarding the heuristic function, we would have a set up similar to the following:

- we have a model for probabilities/likelihoods that describes how likely a material is to be present in a given environment (whether at the borders of an observation, a certain grid size, etc.)
- we have an the spiral search as defined earlier to check if there are any materials present in the observation area
- if nothing is in the area, we use an A* search over environments at the edge of the agent's observation
    - in this A* search, the costs of the heuristic funtion will be the inverses of the probabilities/likelihoods, which would mean that environments with a high probability of containing the materials we're interested in have low cost (and higher priority), while environments that contain no materials we desire have an infinite cost (and if they have low lieklihoods themselves, we'd prefer those environments that often border other environments with high likelihoods)

The above will also be how we train the agent, by having it learn the types of environments that are likely to contain various materials, and refining the likelihood values for a given environment.

We may also add weights to the required materials themselves as a set of trainable parameters to allow the possibility of different acquisition orders, which may also help reduce the time for the overall journey.

As mentioned above under navigation, we also plan to implement 3D navigation, as well as having a joint combination of Dijkstra's Algorithm and the currently implemented return stack perform the calculation for a return path as well.

The current model being a discrete model is restricted in movements, to improve on that and better perform in a "real" Minecraft world, we plan to implement continuous momvement  as well. Crafting elements is achieved as required, the remaining goal for that is for the user to input the item needed and the agent recognizes which available elements are needed from the current terrain/world, then subsequently retrieve them and craft the item.

A challenge we expect to face is to build an algorithm that can irrespective of the world the agent is deployed in, can navigate around obstacles/natural elements present in the world without breaking or compromising on efficiency.
