---
layout: default
title: Status
---

Copied and pasted from the doc for easy reference:

- Project Summary: Since things may have changed since proposal (even if they haven’t), write a short paragraph summarizing the goals of the project (updated/improved version from the proposal).
- Approach: Give a detailed description of your approach, in a few paragraphs. You should summarize the main algorithm you are using, such as by writing out the update equation (even if it is off-the-shelf). You should also give details about the approach as it applies to your scenario. For example, if you are using reinforcement learning for a given scenario, describe the setup in some detail, i.e. how many states/actions you have, what does the reward function look like. A good guideline is to incorporate sufficient details so that most of your approach is reproducible by a reader. I encourage you to use figures for this, as appropriate, as we used in the writeups for the assignments. I recommend at least 2-3 paragraphs.
- Evaluation: An important aspect of your project, as we mentioned in the beginning, is evaluating your project. Be clear and precise about describing the evaluation setup, for both quantitative and qualitative results. Present the results to convince the reader that you have a working implementation. Use plots, charts, tables, screenshots, figures, etc. as needed. I expect you will need at least a 1-2 paragraphs to describe each type of evaluation that you perform.
- Remaining Goals and Challenges: In a few paragraphs, describe your goals for the next 4-5 weeks, when the final report is due. At the very least, describe how you consider your prototype to be limited, and what you want to add to make it a complete contribution. Note that if you think your algorithm is quite good, but have not performed sufficient evaluation, doing them can also be a reasonable goal. Similarly, you may propose some baselines (such as a hand-coded policy) that you did not get a chance to implement, but want to compare against for the final submission. Finally, given your experience so far, describe some of the challenges you anticipate facing by the time your final report is due, how crippling you think it might be, and what you might do to solve them.
- Resources Used: Mention all the resources that you found useful in writing your implementation. This should include everything like code documentation, AI/ML libraries, source code that you used,  StackOverflow, etc. You do not have to be comprehensive, but it is important to report the ones that are crucial to your project. I would like to know these so that the more useful ones can be shared with others in the course.


My preliminary content:
- Project_summary: rip and update from proposal (possibly the same one from index.md)
- Approach: rip from proposal also, but also add in the backtracking, and what exactly our plans are for agent updates (should probably use off-the-shelf or something basic like gradient descent, and this would liekly apply to the bayesian parameter of the search e.g. stone here means x, y, z probabilities of wood, water, sand nearby. The weights to be updated would be the probabilities in this case.)
- Evaluation: rip from proposal; we're using time estimates largely, since there's not really a score otherwise; if the agent is working properly, it will always get the items (if available) and always craft the request (if possible). Since we need to convince of a working demo, once we get the simple Dijkstra's demo down, we can time it on different scenarios and go from there.
- Remaining goals: well, everything that isn't implemented by the time this is written, really. Off the top of my head: A* for the search (instead of dijkstra), bayesian/markov chain for parameters to A* (effectively the inverse costs for the search), and then the weights themselves for the bayesian. We may also want weights for determining item acquisition order (probably fastest to do as many as nearby at a time; e.g. when looking for wood, and finding a tree, if we need more than one wood, just deforest the whole area instead of moving on to another material)
- Do we have any so far? I would guess we will need a guide/resource to implement gradient descent, A* is common enough that we won't need to, might need a resource for bayesian/markov. Probably wouldn't cite the Malmo docs either.

We also need a video with:
- brief description (with media): should be relatively straightforward
- example capture: probably a run of our demo version with full observability
- can include summary to pad time if so desired, but there's a 3 min cap, so maybe not.
- essentially the video is a summary of the status doc (above), with a video of a demo and some pictures/screenshots.
