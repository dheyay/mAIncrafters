---
layout: default
title: Final Report
---

## Project Video

## Project Summary
Suppose you are playing Minecraft and as a regular miner in a world, you want to start a large building project but are not sure about everything you need for it. What if you want to focus on exploring, but need complex items to progress? That is where our mAinCrafter comes in. Our agent focuses on automation of menial tasks in Minecraft to make the gameplay more streamlined and less repetitive for the player. The agent does the finding, mining, and crafting so you can focus on desigining your latest masterpiece.

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/111565913-733abb00-8759-11eb-8345-7286290a9456.png">
</p>

The main goal of this project is to allow the user to give the agent items to craft and the agent will automatically move around and seek out the materials needed to craft it and acquire them. The agent will take into account the placing of the elements and if the item needed to be crafted has a sub-element that also needs crafting, it will find all the base elements needed and provide the user with the final element after crafting it. The agent will be able to find the elements in a large/complex map while avoiding obstacles and being efficient about time as well. It can also be used in order to gather materials stated by the user. 
For example, before building a castle, the user can simply instruct the agent to gather wood or cobblestone. Alternatively, if you want to make a complex items and don't want to deal with tracking down obscure crafting materials, you can simply start the agent and let it run while you can focus on other things.

## Approaches
Our approach to the problem is divided into multiple parts with each part having a unique problem for the agent to tackle.

### Baseline

##### Locating
For locating objects, the baseline version of the agent uses greedy search composed of a spiral search though the observation level that is in the same plane as the agent (the agent has an observation grid equivalent in size to the world), then using Dijkstra's algorithm to find the best path to the found destination. The way it works is to iterate in a direction along the grid until it hits a "corner" spcace in the grid, then changes direction ([Source: StackOverflow](https://stackoverflow.com/questions/398299/looping-in-a-spiral)). This allows us to find one of the closest locations with a material of interest, while avoiding a slower search that does a true check for absolute closest, at which point the agent determines the shortest path there, then goes to collect the material. After this material is collected, this is repeated, checking for the closest material to the current location that we are interested in. If either all necessary materials are gathered or there are no more materials neaby, it returns to the starting point, and effectively restarts the search from there. This allows the agent to avoid missing any blocks that end up outside of the observation window after moving in a given direction.


##### Navigating
Dijkstra's shortest path Algorithm was used as our method of navigation for the baseline once we have determined the location of the object we are looking for. We used Dijkstra's algorithm to find the path between the agent's current location and some material location in two dimensions. As the environment got more complex, Dijkstra's was also used to find the return path from the agent's current location to the starting position.

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

Dijkstra's was used as a baseline since it is relatively easy to implement, and provides solid results. It also serves a basis with which to compare the A* component of our agent. However, it is also guaranteed to produce the path necessary.

Additionally, in our generated world there were a variety of obstacles in the forms of pillars on the map. While navigating, the agent had to be sure to strictly avoid these, rather than merely run into them and adjust, since we included cacti as obstacles as well. If the agent were allowed to run into obstacles, it'd be possible for the agent to kill itself on the cacti before reaching its goal. With this in mind, the agent strictly avoids obstacles while checking for the shortest path (specifically: could not just have an agent run directly to the location).

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/107836543-6853cb80-6d52-11eb-81de-d6ad897d4cd8.gif">
</p>


##### Recipe Formulation and Crafting
Malmo provides functions to craft items. However, there is no feature that examines recipes for the materials required. To do so, we found the files provided by Minecraft itself, and found the base code. By developing a file analysis code, we were able to open and extract the recipe from each of the files (1 for each craftable item). Once we got the information, we placed it into one large dictionary in python, with each variable name as the key and the recipe as the value (a list with a tuple containing the material name and quantity for each ingredient). 

Using information we learned from the Malmo examples, we then find a way to actually craft the items. The function begins with analyzing the inventory, to see what materials we already have. Once we know this, we examine the recipe by checking the dictionary, and for each item required, we check the quantity required and subtract the amount we have in the inventory. Then we recursively call the craft function until we reach an item that is not in the recipe dictionary (therefore cannot be crafted and must be found in the game, like logs, or cobblestone). The agent must find these items. From there, we begin to craft each component, sometimes having to go through many iterations of crafting until we reach the intended item. For example: if we send the craft function for a stone pickaxe, it would recursively search for 3 cobblestone, and for 2 sticks. If they are not in the inventory, it would send the agent to look for cobblestone, and for a log since the log is used for planks which is how you make sticks which is how you make the pickaxe)

Source: [Malmo By Microsoft](https://github.com/microsoft/malmo)

### Final Approach

##### Locating
For locating objects, in this version of the agent we now provide it the biome/material probabilities, and it decides the best biome to search through based on the materials it needs and its current location, which allows it to select biomes that are sufficiently supplied with materials (as per its requirements), while at the same time avoiding going entirely across the map for "extra" materials when it could get a sufficient amount by travelling between two neighboring biomes. Upon choosing the initial biome, the agent uses the same greedy search as the baseline, except it uses A* instead of Dijkstra's, so we'll avoid repeating the entire process here, in favor of detailing A* below. 

To elaborate a bit more on the probabilities, we had a biome to material mapping, where each material in the biome in turn mapped to a probability of being generated in the map. The world is generated using these probabilities, and the agent has access to them for the purpose of choosing which biome should be its destination after each successive material is gathered. In this sense, the agent "knew" what to expect, and even with full access to the map, still used this method for planning successive paths. 

For our final agent, we decided against reducing the observation spaceas intitially planned in the status update, instead making it more of an optimization problem than a learning. This allowed us to focus more on the idea of the agent using prior knowledge to navigate an environment, as well as on the pathfinding and navigation optimizations instead.

We initially attempted to create another baseline that would fully utililize the fully-observed environment (a la Traveling Salesman), but as we were testing it on larger and larger worlds (50x50 was the size of the status world, while we are using 100x100 here), while it charted the most efficient path and thus had the shortest travel time, its computation time far exceeded what would have been necessary to be competitive with even the Dijkstra's baseline, and so further development was halted, since it as the world size grew, the agent using this method would only perform poorer and poorer. This also solidified our position using the probabilities to provide an estimate of the best start, and then using a greedy search within the environment that the agent expected to yield the best results.


##### Navigating
Our agent uses the A* algorithm for navigating and shortest path finding. The A* search is a graph traversal algorithm used for its optimality, completeness and efficiency. Being an uninformed search it is formulated in terms of a weighted graph, which in the agent's case is the observable environment, starting from a specific node. The main aim is to find the path to the goal node with the shortest cost. It does this calculation by maintaining a tree of paths and choosing which nodes from the tree to extend/follow. 


Our implementation of the A* uses a priority queue to perform the continuous selection of the estimated minimum cost nodes to select and expand. It does this selection based on the cost of the path and an estimate of the cost required to extend the path all the way to the goal. Specifically, A* selects the path that minimizes

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/111053426-70b62980-8418-11eb-88ab-4991b8b00839.png">
</p>

where n is the next node on the path, g(n) is the cost of the path from the start node to n, and h(n) is a heuristic function that estimates the cost of the cheapest path from n to the goal. 

A* terminates when the path it chooses to extend is a path from start to goal or if there are no paths eligible to be extended. The heuristic function we use is euclidean distance between two nodes. 

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/111053439-888dad80-8418-11eb-84e4-c718aa2442ed.png">
</p>

Typical implementations of A* use a priority queue to perform the repeated selection of minimum (estimated) cost nodes to expand. This priority queue is known as the open set or fringe. At each step of the algorithm, the node with the lowest f(x) value is removed from the queue, the f and g values of its neighbors are updated accordingly, and these neighbors are added to the queue as the pseudo code below specifies. The algorithm continues until a removed node (thus the node with the lowest f value out of all fringe nodes) is a goal node. The f value of that goal is then also the cost of the shortest path, since h at the goal is zero.

```
while(openset not empty): 
        current = openset.pop() #Gets the node with the lowest F value from the priority queue
        
        if current node == goal node:
            return shortest path
        
        Add current node to closed set
        
        for neighbor in get_neighbors(current node):
            if neighbor in closed set:
                continue 
            
            tentativeG = g value of current node + 1
            
            if neighbor not in open set:
                add neighnbor to open set
             elif tentativeG >= neighbor.g:
                continue
            
            neighbor.parent = current
            neighbor.g = potentialG
            neighbor.h = Euclidiean_distance(neighbor, dest_node)     #Hueristic used to calculate h(n)
            neighbor.f = neighbor.g + neighbor.h
```

As shown, the A* search is an effective method of finding the shortest path on complex maps because every iteration gets the agent closer to the element it has to mine instead of wasting computation time on searching every node in the vicinity of itself. The distance between the agent and the destination is shortened every time a path is extended, ultimately giving us the absolute shortest path while being time efficient which is faster and more accurate than the Dijkstra's for larger maps and more spread out maps.

As with the Dijkstra's baseline, this agent had to navigate around obstacles that had the potential to harm, and so had to be strictly accurate in terms of navigation path, otherwisse it would have been possible for the agent to die in the middle of a run (specifically: could not just have an agent run directly to the location).

<p align="center">
  <img src="https://upload.wikimedia.org/wikipedia/commons/5/5d/Astar_progress_animation.gif">
</p>

[Source: WikiPedia](https://en.wikipedia.org/wiki/A*_search_algorithm#/media/File:Astar_progress_animation.gif)

##### Crafting

Using the same method as in the baseline, we used the files from the Minecraft base code, and used it to extrapolate the recipes for all items in the game. We expand upon the crafting code implemented in the baseline, where we search the inventory, and craft the items we do not already have recursively. Adding onto what we already have, we added a function to return the base materials the items will need, excluding the items already in the inventory. For example, if we ask for a stick, it would recursively search the recipes until it found that a stick is made from 2 planks, which can be made from a log. So the function would return a list of 'log'. This list is later passed onto the agent to find targets for its path.
```
craft(item):
	if item is in inventory:					#We already have the item
		return		
	if item is in recipe_list:					#Item can be broken down into subcomponents
		for each required_item in recipe:
			for necessary quantity of required_item:	
				craft(item)				#Recursion: Make all required subcomponents of each item
	agent.sendCommand('craft "+item)



crafting_requirements(crafting_list):								
	for item in crafting_list:							
		if item in inventory:							#We already have the item
			skip
		else:
			add to required_item_list					#Need to craft that item
	while(items in required_item_list can be simplified into subcomponents):	#Have not yet simplified all in crafting list to base materials
		for items in required_item_list:
			if item in recipe_list:
				for each base_item in recipe:
					for necessary quantity of base_item:
						add base_item to required_item_list	#Add base materials to list
				remove item from recipe_list				#Remove complex item from search list
	
	return required_item_list							#return list of items to search for
```
The above code is a very simplified psuedocode. In reality, there are several exceptions that must be handled. It came to our attention that some items, when crafted, output multiple of the desired item. For example, if we wanted 2 sticks, it would look at the first stick, and deduce it needed a log, and would do the same for the second. However, this would output 2 logs, when in reality, one log provides 4 planks, and 2 planks provide 4 sticks, so we really only need 1 log. This was now accounted for in the function. We also now account for items that change name when gathered. For example, when searching for diamond_ore, after mining it, it turns into just diamonds. So when searching for the next item to find, the agent will see diamond_ore in the search list, and no diamond_ore in the inventory, only diamond. This was had to be accounted for manually, since there were only 4 blocks this applied to.

## Evaluation
#### Time Taken:
The time spent should be minimized. The AI can be considered successful if it approaches or is better than the time spent by an average human on the same task.  We ran a test run between the base agent that gets the work done and our final agent that is more efficient in a generated world with identical variables and raw material distribution. The difference between the times recorded is a good measure of how fast our agent is at doing the same tasks, i.e. finding, acquiring and crafting the required items. The agent is always faster than the baseline even though the elements around the map are scattered and generated randomly.

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/111566408-55218a80-875a-11eb-9f7d-fd48801387b3.png" width="500" height="300">
</p>

Another place where the agent is always successful is against a human doing the same task, an average human would take upwards of 3 minutes on a map where the Final Agent takes 1/3rd of that time. On a larger map, the time difference would only increase in the favour of the agent. The pathfinding and element locating attribute of the agent aids its accuracy in doing its task.

#### Accuracy: 
The measure of how close the AI is to completing the task. If all necessary materials are not available, it will be judged on how close it was to accomplishing the task, i.e. finishing all the other subtasks.

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/111568418-f2ca8900-875d-11eb-84ae-2ca3afd35c32.jpg" width="400" height="235">
</p>

The agent here is still collecting the raw materials needed for crafting, once it does, it will craft them and the items crafted will be available in the inventory for the agent. This can be considered a successful crafting run for the agent. If an element cannot be found on the map, the agent will go on to get the rest of the elements needed and craft all items that can be crafted from the available materials. The above agent was given the following items to craft: [ladder, crafting table, sword, redstone_torch]. 

<p align="center">
  <img src="https://user-images.githubusercontent.com/43485198/111568536-2d342600-875e-11eb-8ded-1a7acd223d38.jpg" width="400" height="235">
</p>

After it's search, it only found enough materials to craft the ladder, crafting table and the redstone torch. Due to lack of materials the sword could not be crafted. This highlights the accuracy of the agent in terms of what needs to be crafted and how many elements are available in the environment.
