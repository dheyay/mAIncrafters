---
layout: default
title: Proposal
---

## Summary of Project

For our project in Minecraft AI, we will be focusing on navigation and automation of menial tasks in Minecraft in order to make the game more streamlined and less repetitive. The main goal of this project is to allow the agent to be given a user crafting recipe, and the agent will automatically move around and seek out the materials needed to craft it and gather them accordingly, and at advanced levels, would be able to craft the recipe on its own and navigate more complex maps. It can also be used in order to just gather materials defined by the user. For example, before a large building project, the user can simply tell it to collect wood or cobblestone, and start the AI.

This can be applied to a full game, allowing the player to automate the menial tasks, such as harvesting food and supplies, or crafting complex items. This would allow the player themselves to focus on more interesting tasks like building and exploring.

## AI/ML Algorithms
Djikstra’s to help map back the shortest route to the materials required and to the crafting station
Dynamic Programming to help chart out where certain blocks and materials are
Natural language processing for the user-defined tasks
If using “natural” worlds (ones that are generated in the same way as base game worlds), a markov model or naive bayes classifier to train the agent on what to expect in a given area. (such as “Trees-> find wood”, “stone by water-> dig down for a mine”, “sand->cactus nearby”, and so on)
Depending on our evaluation metrics, we could opt for route planning via some sort of search after mapping out an area (like alpha/beta pruning), or we could just apply the markov chain as the agent moves (similar to naive bayes above). Potentially have data files for each region (in a larger scale world) so as to not run out of space and ensure the agent has a working memory of the route home as well as material locations.


## Evaluation Plan

#### Metrics:
Time spent on task: The time spent should be minimized. The AI can be considered successful if it approaches or is better than the time spent by an average human on the same task.

#### Distance travelled: 
The amount of distance traveled by the agent should also be minimized. This can be compared to the amount of distance traveled by a human player who has not plotted out their exact path, unlike the AI.
Accuracy: The measure of how close the AI is to completing the task. If all necessary materials are not available, it will be judged on how close it was to accomplishing the task, i.e. finishing all the other subtasks.

#### Baseline:
The baseline for both metrics will be the time and distance spent by an average user. If the AI is within 150% the standard baseline, it can be regarded as successful.

### Stages of Full Functionality:

##### Stage 1: 
Gather materials for something basic: like wood logs for wood planks. The most basic test: requiring the agent to travel to the wood log and break it, and place it into the inventory.
![stage 1](images/stage 1.png?raw=true)

##### Stage 2: 
Gather materials for complex items: Iron ore for iron ingots for iron pickaxe. Here the agent needs to use the particular type of tool required to gather iron ore, adding another layer of complexity.

##### Stage 3: 
Craft items once all materials are in inventory and after having navigated to the crafting table. The layout would be the same as in stage 2, but would require the agent to move to the crafting table and construct items according to a recipe.

##### Sanity cases include: 
Succeeding if it starts with the requested item
Succeeding if it starts with the requested item away from base, then returns
Visualization as an inventory management problem, with the agent mapping and exploring the world. If the agent is wandering in circles, something is wrong; if the agent is returning without the materials, something is wrong; if it’s eating resources with no return, something is wrong (assuming allowed); etc.
Moonshot case: agent consistently and by a large margin outperforms us
