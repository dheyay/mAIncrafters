---
layout: default
title:  Home
---

![maincrafters](https://user-images.githubusercontent.com/43485198/107835889-e367b280-6d4f-11eb-8a03-7c4dcf99a6b0.png)

### Project summary
Our project enables our agent, Steve, to find resources on the user-generated terrain (currently flat), locate these resources present and chart a path to them for the user. Once Steve has found the items/resources available on the map that are needed, he navigates to these objects one by one and mines them, collects them. He continues this until there are no more objects to mine, then returns home to craft a new item from the retrieved resources. The item to be crafted can be specified by the user depending on the resources available in the given map area.

Some project specific screenshots here - current world if possible

### Our plan going ahead
We have planned on using different search/pathfinding algorithms (e.g A*) and adding more complexity to the map by adding obstacles to improve navigation, an improvement in time/movement efficiency for charting the course as the agent learns from previous runs to retreive all resources and craft the item needed by the agent. 

[Find our source code for the agent here](https://github.com/dheyay/mAIncrafters)

More useful links related to our project:

- [Project Proposal](proposal.html)
- [Project Status](status.html)
- [Final](final.html)

Add in the screenshots from the proposal here, as well as some new ones from the current world version

We'll need to get a small working demo, so we can use Dijkstra's on a fully observable world and record the agent going to a block, breaking it, and then returning. Should be simple enough, and I can do it tomorrow (technically today).

It looks like we also need to label our meeting time(s) here.
