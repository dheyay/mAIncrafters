---
layout: default
title: Status
driveId: 1m36ikc72ETu3XMzEmuN3-IHNOu2gZTHv
---

## Project Summary
For our project in Minecraft AI, we will be focusing on navigation and automation of menial tasks in Minecraft in order to make the game more streamlined and less repetitive. The main goal of this project is to allow the agent to be given a user crafting recipe, and the agent will automatically move around and seek out the materials needed to craft it and gather them accordingly. For a more improved version of the agent, a more complex map with obstacles/natural elements specific to the terrain will be used as the agent will have to not only navigate to the resources but also avoid different obstacles and natural structures in the way while also being efficient about time.  It can also be used in order to just gather materials defined by the user. For example, before a large building project, the user can simply tell it to collect wood or cobblestone, and start the AI.

*INCLUDE VIDEO*
{% include googleDrivePlayer.html id=page.driveId %}

## Approach
Our approach to the problem is divided into multiple parts with each part having a unique problem for the agent to tackle.

#### Locating
For locating objects, the current version of the agent uses a spiral search though the observation level that is in the same plane as the agent (at this point in time, the agent has an observation grid equivalent in size to the world). The way it works is to iterate in a direction along the grid until it hits a "corner" spcace in the grid, then changes direction [Source: StackOverflow](https://stackoverflow.com/questions/398299/looping-in-a-spiral). This allows us to find the closest location with a material of interest, at which point the agent determines the shortest path there (using Dijkstra's algorithm, then goes to collect the material. After this material is collected, this is repeated, checking for the closest material to the current location. If nothing is found nearby, it currently returns to the starting point, and effectively restarts the search from there. This allows the agent to avoid missing any blocks that end up outside of the observation window after moving in a given direction.

As the basic functions of the agent are confirmed and solidified, the observation window will be reduced to better mimic a player's view. As a result of this restriction, it will be entirely possible that no desired materials are observable from the starting point of the agent, and this is where the AI will come into play. More details will be in the Remaining Goals and Challenges section, but the short version is that we will be training the agent to associate various world characteristics and landscapes with materials, and have the agent move towards regions that are likely to contain the object in its searches.

#### Navigating
Dijkstra's shortest path Algorithm is currently used as our method of navigation once we have determined the location of the object we are looking for. As it stands currently, we use Dijkstra's algorithm to find the path between the agent's current location and some material location in two dimensions, while we have a stack implemented to keep reccord of the current shortest path back. As the environment get more complex, Dijkstra's will also be used to find the return path from the agent's current location to the starting position.

Dijkstra's shortest path for the agent: 
The way we are using Dijkstra's Algorithm in are project is as follows:
- set the starting location and destination, and have a current space used to keep track of position, which starts at the starting location
-- the cost to travel to the starting location is 0, and the cost for every other space defaults to infinity
- iterate over the spaces that are adjacent to the current space
-- if the cost of travelling to that space is greater than 1 + the cost to the current space, then the next space's cost is set to (1 + cost of current space), and it's previous space is set to the current space.
- this repeats, updating the current space as it calculates, and finally results in a mapping of (space_loaction) -> (cost, previous_space) for all relevant spaces
- starting from the destination space, we then get the path by recording the the previous spaces of each space in the path until we reach the starting location
- finally, the actions necessary for the agent to travel that path are extracted

In the current version of the agent, once the path is found and the agent moves to the location, the material in question is collected (if the material is a block, the agent breaks the block, then collects), and the location algorithm then Dijkstra's Algorithm are run in succession repeatedly until no nearby blocks are found, at which point the agent returns to the starting position.

In the gif below, there is a visualization of Dijkstra's algorithm being used to find a path while an obstacle is in the way. This will be quite relevant to our agent, since when generating paths, there will be choices to either consider a block as an obstacle blocking us or something that is climbable (for a 3D implementation of Dijkstra's Algorithm), and even if climbable, if there is still a route to the destination beyond it.

![Dijkstras_progress_animation](https://user-images.githubusercontent.com/43485198/107836543-6853cb80-6d52-11eb-81de-d6ad897d4cd8.gif)

[Source: WikiPedia](https://en.wikipedia.org/wiki/File:Dijkstras_progress_animation.gif)

#### Recipe Formulation and Crafting

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
The main goal that remains is to improve the pathfinding algorithm and compare results to see which is the best performing algorithm with time being the evaluating factor. We may use a version of the A* search to do that while also using a bayesian/markov chain implementation for parameters to the A* search. Adding weights to the required elements for determining the order of their acquisition would also help reducing the time for decision making during the navigation process. 
The current model being a discrete model is restricted in movements, to improve on that, a better model with a continouous momvement pattern is to be added as well. Crafting elements is achieved as required, the remaining goal for that is for the user to input the item needed and the agent recognizes which available elements are needed from the current terrain/world, then subsequently retrieve them and craft the item.
A challenge we expect to face is to build an algorithm that can irrespective of the world the agent is deployed in, can navigate around obstacles/natural elements present in the world without breaking or compromising on efficiency.


--- DELETE LATER
My preliminary content:
- Project_summary: rip and update from proposal (possibly the same one from index.md)
- Approach: rip from proposal also, but also add in the backtracking, and what exactly our plans are for agent updates (should probably use off-the-shelf or something basic like gradient descent, and this would liekly apply to the bayesian parameter of the search e.g. stone here means x, y, z probabilities of wood, water, sand nearby. The weights to be updated would be the probabilities in this case.)
