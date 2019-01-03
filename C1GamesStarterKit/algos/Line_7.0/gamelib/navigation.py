import heapq
import math
import sys
import queue
import time
import gamelib
from .game_map import GameMap
from .unit import GameUnit
from .util import debug_write

class Coord:
    def __init__(self, loc):
        if len(loc) == 2:
            self.loc = loc
        else:
            self.loc = [-100, -100]
        
    
    def __getitem__(self, is_y):
        if is_y:
            return self.loc[1]
        return self.loc[0]


    def __setitem__(self, val):
        if len(val) == 2:
            self.loc = val

class Node:
    """A pathfinding node

    Attributes:
        * visited_idealness (bool): Have we visited this node during the idealness search step?
        * visited_validate (bool): Have we visited this node during the validation step?
        * blocked (bool): Is there a firewall at this node's location
        * pathlength: The distance between this node and the target location

    """
    def __init__(self, x=-1, y=-1, tr=-1, tl=-1, bl=-1, br=-1, temptr=True, temptl=True, tempbl=True, tempbr=True):
        self.x = x
        self.y = y
        self.tr = tr
        self.tl = tl
        self.bl = bl
        self.br = br

        # Dir:
        # 0: tr
        # 1: tl
        # 2: bl
        # 3: br
        self.dist = [tr, tl, bl, br]
        self.temp = [temptr, temptl, tempbl, tempbr]

        self.visited_idealness = False
        self.visited_validate = False
        self.blocked = False
        self.pathlength = -1

class PathFinding(GameMap):

    def __init__(self, config, storage):
        #from .game_map import get_edges

        super(PathFinding, self).__init__(config, storage)
        
        self.pathfinding_map = []

        for x in range(0, self.ARENA_SIZE):
            self.pathfinding_map.append([])
            for y in range(0, self.ARENA_SIZE):
                self.pathfinding_map[x].append(Node(x, y))
                
        self.calculated = False

        self.storage = storage

    def calculate(self):

        self.pathfinding_map = []

        for x in range(0, self.ARENA_SIZE):
            self.pathfinding_map.append([])
            for y in range(0, self.ARENA_SIZE):
                self.pathfinding_map[x].append(Node(x, y))

        start_time = time.clock()
        #`gamelib.debug_write("Starting pathfinding calculation")


        # Start from edges
        i=0
        #gamelib.debug_write("Starting edgy stuff")

        changed_locs = set()

        for edge in self.edges:
            if i == 0:
                dTR = 1
            else:
                dTR = -1
            if i == 1:
                dTL = 1
            else:
                dTL = -1
            if i == 2:
                dBL = 1
            else:
                dBL = -1
            if i == 3:
                dBR = 1
            else:
                dBR = -1
            i += 1

            for edge_loc in edge:
                x, y = edge_loc[0], edge_loc[1]
                self.pathfinding_map[x][y] = Node(x, y, dTR, dTL, dBL, dBR, not bool(dTR), not bool(dTL), not bool(dBL), not bool(dTR))
                if self.contains_stationary_unit(edge_loc):
                    Node.blocked = True
                else:
                    changed_locs.add(Coord(edge_loc))

        gamelib.debug_write("Edges took {}s".format(time.clock()-start_time))


        #for i in range(1, self.HALF_ARENA**2):
        #    start_time_2 = time.clock()
        #    any_changed = False
        #    for x in range(0, self.ARENA_SIZE):
        #        for y in range(0, self.ARENA_SIZE):
        #            #if i == 4:
        #            #    gamelib.debug_write("Expanding location ({}, {})".format(x,y))
        #            if self.in_arena_bounds([x, y]):
        #                if i in self.pathfinding_map[x][y].dist and not self.contains_stationary_unit([x, y]):
        #                    changed = self.propogate_node([x, y])
        #                    if len(changed) > 0:
        #                        for loc in changed:
        #                            if loc not in changed_nodes:
        #                                new_changes.add(loc)
        #                        if not any_changed:
        #                            any_changed = True

        self.propogate_from_set(changed_locs)

        gamelib.debug_write("Did original propogation")

        # Check for missing spots
        in_arena_bounds = self.in_arena_bounds

        missing = True
        best_loc = [None, None, None, None]
        x_value_less = [False, True, True, False]
        
        while missing:
            missing = False

            to_prop = set()

            for x in range(0, 28):
                for y in range(0, 28):
                    if in_arena_bounds([x, y]) and not self.contains_stationary_unit([x, y]):
                        for i in range(0, 4):
                            if self.pathfinding_map[x][y].dist[i] == -1:
                                # Check against best node
                                if best_loc[i] == None or y > best_loc[i][1] or (y == best_loc[i][1] and ((x > best_loc[i][0]) != x_value_less[i])):
                                    best_loc[i] = [x, y]
                                    if not missing:
                                        missing = True

            if missing:
                gamelib.debug_write("o no something missing")
                i=0
                for loc in best_loc:
                    if loc != None:
                        to_prop.add(Coord(loc))
                        self.pathfinding_map[loc[0]][loc[1]].dist[i] = 1
                        self.pathfinding_map[loc[0]][loc[1]].temp[i] = True

                    i += 1

                self.propogate_from_set(to_prop, True)
        
        gamelib.debug_write("Finished 'missing' values")


        self.calculated = True
        end_time = time.clock()

        gamelib.debug_write("Calculated pathfinding in {}s".format(end_time-start_time))


    def propogate_from_set(self, locs, temp=False):

        changed_locs = locs
        new_changes = set()
        i=0
        while True:
            #start_time_2 = time.clock()
            #gamelib.debug_write("we looping at i={} and len={}".format(i, len(changed_locs)))
            any_changed = False

            for coord in changed_locs:
                #gamelib.debug_write("Trying with new set of changes")
                local_changes = self.propogate_node(coord.loc)
                if len(local_changes) > 0:
                    #gamelib.debug_write("{} changes".format(len(local_changes)))
                    for loc in local_changes:
                        new_changes.add(Coord(loc))
                    #gamelib.debug_write("Made changes set")
                    if not any_changed:
                        any_changed = True
                #gamelib.debug_write("Done with this set of changes")


            if not any_changed:
                #gamelib.debug_write("i = {} took {}s to compute. Nothing happened.".format(i, time.clock()-start_time_2))
                break
            else:
                changed_locs = set(new_changes)
                new_changes = set()
                #gamelib.debug_write("i = {} took {}s to compute".format(i, time.clock()-start_time_2))
            i+=1
            


    def propogate_node(self, loc):

        x, y = loc[0], loc[1]
        locs = [[x, y+1], [x, y-1], [x-1, y], [x+1, y]]
        any_changed = False

        further_propogations = []

        in_arena_bounds = self.in_arena_bounds
        pathfinding_map = self.pathfinding_map
        propogate_node = self.propogate_node
        contains_stationary_unit = self.contains_stationary_unit

        dirs = []

        node_dist = pathfinding_map[x][y].dist
        node_temp = pathfinding_map[x][y].temp

        for i in range(0, 4):
            if node_dist[i] != -1:
                dirs.append(i)
        
        for new_loc in locs:
            if not in_arena_bounds(new_loc):
                continue

            loc_change = False

            next_node = pathfinding_map[new_loc[0]][new_loc[1]]

            for i in dirs:
                if next_node.dist[i] == -1 or (next_node.temp[i] and not node_temp[i]):# or next_node.dist[i] > node_dist[i] + 1:
                    next_node.dist[i] = node_dist[i] + 1
                    next_node.temp[i] = node_temp[i]
                    if not any_changed:
                        any_changed = True
                    if not loc_change:
                        loc_change = True

            if loc_change and not contains_stationary_unit(new_loc):
                further_propogations.append(new_loc)

        return further_propogations

    """

    def propogate_node(self, loc, chain_propogation=False):

        in_arena_bounds = self.in_arena_bounds
        pathfinding_map = self.pathfinding_map
        propogate_node = self.propogate_node
        contains_stationary_unit = self.contains_stationary_unit

        x, y = loc[0], loc[1]
        locs = [[x, y+1], [x, y-1], [x-1, y], [x+1, y]]

        node = pathfinding_map[x][y]
        nodes = []

        any_changed = False

        further_propogations = set()

        for new_loc in locs:
            if in_arena_bounds(new_loc):
                nodes.append(pathfinding_map[new_loc[0]][new_loc[1]])

        for i in range(0, 4):
            for next_node in nodes:
                if node.dist[i] != -1 and (next_node.dist[i] == -1 or next_node.dist[i] > node.dist[i] + 1):
                    new_loc = next_node.x, next_node.y

                    next_node.dist[i] = node.dist[i] + 1
                    if not any_changed:
                        any_changed = True
                    if new_loc not in further_propogations and not contains_stationary_unit(new_loc):
                        further_propogations.add(new_loc)




        for new_loc in locs:
            if not in_arena_bounds(new_loc):
                continue

            loc_change = False


        if chain_propogation and any_changed:
            for next_loc in further_propogations:
                try:
                    propogate_node(next_loc, True)
                except RecursionError:
                    gamelib.debug_write("Too much recursion!")

        return further_propogations



    """

    def copy_pathing(self, map):
        for x in range(0, 28):
            for y in range(0, 28):
                if self.in_arena_bounds([x,y]):
                    for i in range(0, 4):
                        self.pathfinding_map[x][y].dist[i] = self.storage.list[map[x][y].dist[i]]


    def contains_stationary_unit(self, location):
        """Check if a location is blocked

        Args:
            * location: The location to check

        Returns:
            True if there is a stationary unit at the location, False otherwise
        """
        x, y = map(int, location)
        for unit in self.map[x][y]:
            if unit.stationary:
                return unit
        return False

    
    def next_loc(self, unit):

        x, y = unit.x, unit.y

        locs = [[x, y+1], [x, y-1], [x-1, y], [x+1, y]]

        ideal_iter = -1
        highest_score = -1
        locs = [[x, y+1], [x, y-1], [x-1, y], [x+1, y]]
        for loc in locs:
            if not self.in_arena_bounds(loc) or self.contains_stationary_unit(loc):
                #gamelib.debug_write("stationary unit")

                continue

            temp_score = 0
            diff = self.pathfinding_map[x][y].dist[unit.path_target] - self.pathfinding_map[loc[0]][loc[1]].dist[unit.path_target]
            
            if diff < 0:
                #gamelib.debug_write("diff < 0")

                continue

            temp_score += diff

            #gamelib.debug_write("Score: {}".format(temp_score))

            # Change idealness based on whether we want to move vertically or horizontally next
            temp_score += (int(unit.next_dir_up != bool(int(locs.index(loc)/2)))) - 0.5
            #gamelib.debug_write("Score: {}".format(temp_score))

            # Change idealness based on whether we are trying to move closer to our edge
            temp_score += ((int( (loc[0] > x) == (unit.path_target % 3 == 0) )) - 0.5) / 10
            #gamelib.debug_write("Score:{} ".format(temp_score))

            temp_score += ((int( (loc[1] > y) == (unit.path_target < 2) )) - 0.5) / 10
            #gamelib.debug_write("Score: {}".format(temp_score))

            if temp_score > highest_score:
                highest_score = temp_score
                ideal_iter = locs.index(loc)

        if ideal_iter == -1:
            #gamelib.debug_write("Unit at ({}, {}) doesn't want to move".format(x, y))
            return unit.loc
        
        new_loc = locs[ideal_iter]

        #gamelib.debug_write("Unit should move from ({}, {}) to ({}, {})".format(x, y, new_loc[0], new_loc[1]))

        return new_loc


    def show_board(self, edge):

        for y in reversed(range(0, self.ARENA_SIZE)):
            curr_line = "Row {}".format(y)
            if y < 10:
                curr_line += " "

            curr_line += "     "

            for x in range(0, self.ARENA_SIZE):
                temp_string = " "
                if self.in_arena_bounds([x,y]):
                    if self.contains_stationary_unit([x,y]):
                        temp_string += ".  "
                    else:
                        tr = self.pathfinding_map[x][y].dist[edge]
                        temp_string += "{} ".format(tr)

                        if tr < 10:
                            temp_string += " "

                else:
                    temp_string += "   "
                
                curr_line += temp_string

            gamelib.debug_write(curr_line)
            gamelib.debug_write("")


    def print_map(self):
        pass
        """Prints an ASCII version of the current game map for debug purposes

        """
        """
        for y in reversed(range(0, self.ARENA_SIZE)):
                curr_line = "Row {}".format(y)
                if y < 10:
                    curr_line += " "

                curr_line += "     "

                for x in range(0, self.ARENA_SIZE):
                    temp_string = " "
                    if self.in_arena_bounds([x,y]):
                        if self.contains_stationary_unit([x,y]):
                            temp_string += ".  "
                        else:
                             = self.pathfinding_map[x][y].dist[edge]
                            temp_string += "{} ".format(tr)

                            if tr < 10:
                                temp_string += " "

                    else:
                        temp_string += "   "
                    
                    curr_line += temp_string

                gamelib.debug_write(curr_line)
                gamelib.debug_write("")
        """
        


"""
This class helps with pathfinding. We guarentee the results will
be accurate, but top players may want to write their own pathfinding
code to maximise time efficiancy
"""
class ShortestPathFinder:
    """Handles pathfinding

    Attributes:
        * HORIZONTAL (int): A constant representing a horizontal movement
        * VERTICAL (int): A constant representing a vertical movement

        * game_state (:obj: GameState): The current gamestate
        * game_map (:obj: GameMap): The current gamemap

    """
    def __init__(self):
        self.HORIZONTAL = 1
        self.VERTICAL = 2

    def navigate_multiple_endpoints(self, start_point, end_points, game_state):
        """Finds tha path a unit would take to reach a set of endpoints

        Args:
            * start_point: The starting location of the unit
            * end_points: The end points of the unit, should be a list of edge locations
            * game_state: The current game state

        Returns:
            The path a unit at start_point would take when trying to reach end_points given the current game state.
            Note that this path can change if a tower is destroyed during pathing, or if you or your enemy places firewalls.

        """
        if game_state.contains_stationary_unit(start_point):
            return

        #Initialize map 
        self.game_state = game_state
        self.game_map = [[Node() for x in range(self.game_state.ARENA_SIZE)] for y in range(self.game_state.ARENA_SIZE)]
        #Fill in walls
        for location in self.game_state.game_map:
            if self.game_state.contains_stationary_unit(location):
                self.game_map[location[0]][location[1]].blocked = True
        #Do pathfinding
        ideal_endpoints = self._idealness_search(start_point, end_points)
        self._validate(ideal_endpoints, end_points)
        return self._get_path(start_point, end_points)

    def _idealness_search(self, start, end_points):
        """
        Finds the most ideal tile in our 'pocket' of pathable space. 
        The edge if it is available, or the best self destruct location otherwise
        """
        current = queue.Queue()
        current.put(start)
        best_idealness = self._get_idealness(start, end_points)
        self.game_map[start[0]][start[1]].visited_idealness = True
        most_ideal = start

        while not current.empty():
            search_location = current.get()
            for neighbor in self._get_neighbors(search_location):
                if not self.game_state.game_map.in_arena_bounds(neighbor) or self.game_map[neighbor[0]][neighbor[1]].blocked:
                    continue

                x, y = neighbor
                current_idealness = self._get_idealness(neighbor, end_points)

                if current_idealness > best_idealness:
                    best_idealness = current_idealness
                    most_ideal = neighbor

                if not self.game_map[x][y].visited_idealness and not self.game_map[x][y].blocked:
                    self.game_map[x][y].visited_idealness = True
                    current.put(neighbor)

        return most_ideal

    def _get_neighbors(self, location):
        """Get the locations adjacent to a location
        """
        x, y = location
        return [[x, y + 1], [x, y - 1], [x + 1, y], [x - 1, y]]

    def _get_direction_from_endpoints(self, end_points):
        """Prints a message to the games debug output

        Args:
            * end_points: A set of endpoints, should be an edge 

        Returns:
            A direction [x,y] representing the edge. For example, [1,1] for the top right and [-1, 1] for the top left

        """
        point = end_points[0]
        x, y = point
        direction = [1, 1]
        if x < self.game_state.HALF_ARENA:
           direction[0] = -1
        if y < self.game_state.HALF_ARENA:
            direction[1] = -1
        return direction

    def _get_idealness(self, location, end_points):
        """Get the idealness of a tile, the reachable tile the unit most wants to path to.
        Better self destruct locations are more ideal. The endpoints are perfectly ideal. 

        Returns:
            A location the unit will attempt to reach
        """
        if location in end_points:
            return sys.maxsize

        direction = self._get_direction_from_endpoints(end_points)

        idealness = 0
        if direction[1] == 1:
            idealness += 28 * location[1]
        else: 
            idealness += 28 * (27 - location[1])
        if direction[0] == 1:
            idealness += location[0]
        else: 
            idealness += (27 - location[0])

        return idealness

    def _validate(self, ideal_tile, end_points):
        """Breadth first search of the grid, setting the pathlengths of each node

        """
        #VALDIATION
        #Add our most ideal tiles to current
        current = queue.Queue()
        if ideal_tile in end_points:
            for location in end_points:
               current.put(location)
               #Set current pathlength to 0
               self.game_map[location[0]][location[1]].pathlength = 0
               self.game_map[location[0]][location[1]].visited_validate = True
        else:
            current.put(ideal_tile)
            self.game_map[ideal_tile[0]][ideal_tile[1]].pathlength = 0
            self.game_map[ideal_tile[0]][ideal_tile[1]].visited_validate = True

        #While current is not empty
        while not current.empty():
            current_location = current.get()
            current_node = self.game_map[current_location[0]][current_location[1]]
            for neighbor in self._get_neighbors(current_location):
                if not self.game_state.game_map.in_arena_bounds(neighbor) or self.game_map[neighbor[0]][neighbor[1]].blocked:
                    continue

                neighbor_node = self.game_map[neighbor[0]][neighbor[1]]
                if not neighbor_node.visited_validate and not current_node.blocked:
                    neighbor_node.pathlength = current_node.pathlength + 1
                    neighbor_node.visited_validate = True
                    current.put(neighbor)

        #debug_write("Print after validate")
        #self.print_map()
        return

    def _get_path(self, start_point, end_points):
        """Once all nodes are validated, and a target is found, the unit can path to its target

        """
        #GET THE PATH
        path = [start_point]
        current = start_point
        move_direction = 0

        while not self.game_map[current[0]][current[1]].pathlength == 0:
            #debug_write("current tile {} has cost {}".format(current, self.game_map[current[0]][current[1]].pathlength))
            next_move = self._choose_next_move(current, move_direction, end_points)
            #debug_write(next_move)

            if current[0] == next_move[0]:
                move_direction = self.VERTICAL
            else:
                move_direction = self.HORIZONTAL
            path.append(next_move)
            current = next_move
        
        #debug_write(path)
        return path
  
    def _choose_next_move(self, current_point, previous_move_direction, end_points):
        """Given the current location and adjacent locations, return the best 'next step' for a given unit to take
        """
        neighbors = self._get_neighbors(current_point)
        #debug_write("Unit at {} previously moved {} and has these neighbors {}".format(current_point, previous_move_direction, neighbors))

        ideal_neighbor = current_point
        best_pathlength = self.game_map[current_point[0]][current_point[1]].pathlength
        for neighbor in neighbors:
            #debug_write("Comparing champ {} and contender {}".format(ideal_neighbor, neighbor))
            if not self.game_state.game_map.in_arena_bounds(neighbor) or self.game_map[neighbor[0]][neighbor[1]].blocked:
                continue

            new_best = False
            x, y = neighbor
            current_pathlength = self.game_map[x][y].pathlength

            #Filter by pathlength
            if current_pathlength > best_pathlength:
                continue
            elif current_pathlength < best_pathlength:
                #debug_write("Contender has better pathlength at {} vs champs {}".format(current_pathlength, best_pathlength))
                new_best = True

            #Filter by direction based on prev move
            if not new_best and not self._better_direction(current_point, neighbor, ideal_neighbor, previous_move_direction, end_points):
                continue

            ideal_neighbor = neighbor
            best_pathlength = current_pathlength

        #debug_write("Gave unit at {} new tile {}".format(current_point, ideal_neighbor))
        return ideal_neighbor

    def _better_direction(self, prev_tile, new_tile, prev_best, previous_move_direction, end_points):
        """Compare two tiles and return True if the unit would rather move to the new one

        """
        #True if we are moving in a different direction than prev move and prev is not
        #If we previously moved horizontal, and now one of our options has a different x position then the other (the two options are not up/down)
        if previous_move_direction == self.HORIZONTAL and not new_tile[0] == prev_best[0]:
            #We want to go up now. If we have not changed our y, we are not going up
            if prev_tile[1] == new_tile[1]:
                return False 
            return True
        if previous_move_direction == self.VERTICAL and not new_tile[1] == prev_best[1]:
            if prev_tile[0] == new_tile[0]:
                #debug_write("contender {} has the same x coord as prev tile {} so we will keep best move {}".format(new_tile, prev_tile, prev_best))
                return False
            return True
        if previous_move_direction == 0: 
            if prev_tile[1] == new_tile[1]: 
                return False
            return True
        
        #To make it here, both moves are on the same axis 
        direction = self._get_direction_from_endpoints(end_points)
        if new_tile[1] == prev_best[1]: #If they both moved horizontal...
            if direction[0] == 1 and new_tile[0] > prev_best[0]: #If we moved right and right is our direction, we moved towards our direction
                return True 
            if direction[0] == -1 and new_tile[0] < prev_best[0]: #If we moved left and left is our direction, we moved towards our direction
                return True 
            return False 
        if new_tile[0] == prev_best[0]: #If they both moved vertical...
            if direction[1] == 1 and new_tile[1] > prev_best[1]: #If we moved up and up is our direction, we moved towards our direction
                return True
            if direction[1] == -1 and new_tile[1] < prev_best[1]: #If we moved down and down is our direction, we moved towards our direction
                return True
            return False
        return True

    def print_map(self):
        """Prints an ASCII version of the current game map for debug purposes

        """
        for y in range(28):
            for x in range(28):
                node = self.game_map[x][28 - y - 1]
                if not node.blocked and not node.pathlength == -1:
                    self._print_justified(node.pathlength)
                else:
                    sys.stderr.write("   ")
            debug_write("")

    def _print_justified(self, number):
        """Prints a number between 100 and -10 in 3 spaces

        """
        if number < 10 and number > -1:
            sys.stderr.write(" ")
        sys.stderr.write(str(number))
        sys.stderr.write(" ")
