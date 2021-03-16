import heapq
import numpy as np


class Node:

    def __init__(self, parent=None, Pos=None):
        self.parent = parent
        self.pos = Pos
        self.closed = None
        self.opened = None
        self.g = 0
        self.h = 0
        self.f = 0

    def __eq__(self, other):
        return self.pos == other.pos

    def __repr__(self):
        return f"{self.pos} - g: {self.g} h: {self.h} f: {self.f}"

    def __lt__(self, other):
        return self.f < other.f

    def __gt__(self, other):
        return self.f > other.f


# --------------------------------------------------------------------------------------------
# A-Star utility functions

# Return reversed path with 1D grid indices instead of coordinates
def return_path(current_node, obs):
    path = []
    current = current_node
    while current is not None:
        index = (obs * 2 + 1) * (current.pos[1] + obs) + current.pos[0] + obs
        path.append(index)
        current = current.parent
    return path[::-1]


# Check if all blocks are walkable
def get_neighbors(grid, n, obs, dest, allow_diagonal=False):
    offset = (2 * obs + 1) ** 2
    index = (obs * 2 + 1) * (n.pos[1] + obs) + n.pos[0] + obs
    nd = None
    if allow_diagonal:
        nd = [index + ((2 * obs) + 1), index + ((2 * obs) + 1) + 1, index + ((2 * obs) + 1) - 1,
              index - ((2 * obs) + 1), index - ((2 * obs) + 1) + 1, index - ((2 * obs) + 1) - 1,
              index + 1, index - 1]
    else:
        nd = [index + ((2 * obs) + 1), index - ((2 * obs) + 1), index + 1, index - 1]

    filtered = []
    for i in nd:
        if grid[i + offset] == "air":
            filtered.append(i)
        elif i == dest:
            filtered.append(i)

    n_coord = [get_coordinates_from_index(idx, obs) for idx in filtered]
    return n_coord


def sqr_distance(node, dest):
    dx = abs(node.pos[0] - dest.pos[0])
    dy = abs(node.pos[1] - dest.pos[1])
    return np.sqrt(dx * dx + dy * dy)


def get_coordinates_from_index(index, obs_size):
    y = index // (2 * obs_size + 1) - obs_size
    x = index % (2 * obs_size + 1) - obs_size
    return (x, y)


# --------------------------------------------------------------------------------------------
# A-Star search function

def AStar(grid, start, dest, obs_size, allow_diagonal_movement=False):
    """
    Parameters
    ----------
    grid : [int]    ->  1-D flattened array of game world/state
    start : int     ->  Index of grid that corresponds to the starting position
    dest : int      ->  Index of grid that corresponds to the destination
    obs_size : int  ->  Agents observational space
    obstacles : [string] -> Contains a list of obstacles to avoid
    allow_diagonal_movement : bool, optional
                    -> The default is False. Set to true if diagonal movement
                        for agent is allowed
    Returns
    -------
    List of indices of shortest path from start to destination

    """
    start_xy, dest_xy = get_coordinates_from_index(start, obs_size), get_coordinates_from_index(dest, obs_size)
    start_node = Node(None, start_xy)
    dest_node = Node(None, dest_xy)

    start_node.g = 0
    start_node.f = 0

    closed_set = set()
    open_set = []
    heapq.heapify(open_set)
    heapq.heappush(open_set, start_node)

    while (len(open_set) > 0):
        heapq.heapify(open_set)
        current = heapq.heappop(open_set)
        # print("Popped: ", current)

        if current.pos == dest_node.pos:
            return return_path(current, obs_size)

        closed_set.add(current.pos)

        neighbors = get_neighbors(grid, current, obs_size, dest, allow_diagonal_movement)
        for i in range(0, len(neighbors)):
            neighbor = Node(None, neighbors[i])
            if neighbor.pos in closed_set:
                continue

            potentialG = current.g + 1

            if neighbor not in open_set:
                heapq.heappush(open_set, neighbor)
            elif potentialG >= neighbor.g:
                continue

            neighbor.parent = current
            neighbor.g = potentialG
            neighbor.h = sqr_distance(neighbor, dest_node)
            neighbor.f = neighbor.g + neighbor.h

    return None
































