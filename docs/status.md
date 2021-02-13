---
layout: default
title: Status
---

## Project Summary
For our project in Minecraft AI, we will be focusing on navigation and automation of menial tasks in Minecraft in order to make the game more streamlined and less repetitive. The main goal of this project is to allow the agent to be given a user crafting recipe, and the agent will automatically move around and seek out the materials needed to craft it and gather them accordingly. For a more improved version of the agent, a more complex map with obstacles/natural elements specific to the terrain will be used as the agent will have to not only navigate to the resources but also avoid different obstacles and natural structures in the way while also being efficient about time.  It can also be used in order to just gather materials defined by the user. For example, before a large building project, the user can simply tell it to collect wood or cobblestone, and start the AI.

*INCLUDE VIDEO*

## Approach
Our approach to the problem is divided into multiple parts with each part having a unique problem for the agent to tackle.

#### Locating

#### Navigating
For navigating and pathfinding once the resources are located in the map, we are using a version of the famous Dijkstra's pathfinding algorithm. The Dijkstra's algorithm gives the agent a shortest path between it's current location and the location of the item type needed.

Dijkstra's shortest path for the agent: 
*Explain depth with code if  possible*

![Dijkstras_progress_animation](https://user-images.githubusercontent.com/43485198/107836543-6853cb80-6d52-11eb-81de-d6ad897d4cd8.gif)

[Source: WikiPedia](https://en.wikipedia.org/wiki/File:Dijkstras_progress_animation.gif)

Once the shortest path is identified, a path is generated which is then converted into commands which make the agent move towards the block type. Once reached, the block will be attacked until broken, once the item is collected, the shortest path using the same algorithm is found between the agent and the next closest block type needed. This process is repeated until all the required blocks are collected.

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
