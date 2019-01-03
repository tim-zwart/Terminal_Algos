import gamelib
import time
import timeit
import math
from .util import debug_write

class Simulator:
    def __init__(self, config, serialized_string, storage):
        
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, REMOVE, FIREWALL_TYPES, ALL_UNITS, UNIT_TYPE_TO_INDEX
        UNIT_TYPE_TO_INDEX = {}
        FILTER = config["unitInformation"][0]["shorthand"]
        UNIT_TYPE_TO_INDEX[FILTER] = 0
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        UNIT_TYPE_TO_INDEX[ENCRYPTOR] = 1
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        UNIT_TYPE_TO_INDEX[DESTRUCTOR] = 2
        PING = config["unitInformation"][3]["shorthand"]
        UNIT_TYPE_TO_INDEX[PING] = 3
        EMP = config["unitInformation"][4]["shorthand"]
        UNIT_TYPE_TO_INDEX[EMP] = 4
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        UNIT_TYPE_TO_INDEX[SCRAMBLER] = 5
        REMOVE = config["unitInformation"][6]["shorthand"]
        UNIT_TYPE_TO_INDEX[REMOVE] = 6

        ALL_UNITS = [PING, EMP, SCRAMBLER, FILTER, ENCRYPTOR, DESTRUCTOR]
        FIREWALL_TYPES = [FILTER, ENCRYPTOR, DESTRUCTOR]

        self.config = config
        self.game_state = gamelib.AdvancedGameState(config, serialized_string, storage, True)
        self.finished = False
        self.curr_frame = 0

        self.move_times = []
        self.attack_times = []

        self.unit_list = set()
        self.encryptor_list = set()

        self.loc_in_range = self.game_state.game_map.get_locations_in_range([0,0], 3, True)
        self.loc_in_range_1 = self.game_state.game_map.get_locations_in_range([0,0], 1, True)

        self.calculated = False


    def calculate(self):
        self.game_state.game_map.calculate()
        self.calculated = True


    def simulate(self):
        #gamelib.debug_write("New simulation")

        if not self.calculated:
            self.game_state.game_map.calculate()

        #self.game_state.game_map.show_board(self.game_state.game_map.TOP_LEFT)

        for x in range(0, self.game_state.game_map.ARENA_SIZE):
            for y in range(0, self.game_state.game_map.ARENA_SIZE):
                if self.game_state.game_map.in_arena_bounds([x,y]):
                    if not self.game_state.contains_stationary_unit([x,y]) and len(self.game_state.game_map[x,y]) >= 1:
                        for unit in self.game_state.game_map[x,y]:
                            self.unit_list.add(unit)
                    elif len(self.game_state.game_map[x,y]) == 1 and self.game_state.game_map[x,y][0].unit_type == ENCRYPTOR:
                        self.encryptor_list.add(self.game_state.game_map[x,y][0])
        #gamelib.debug_write("Finished making simulation lists. Turn = {}".format(self.game_state.turn_number))
        #timeit self.frame()

        #start_time = time.clock()
        while not self.finished:
            if self.game_state.turn_number == 4:
                gamelib.debug_write("Frame")
            self.frame()
        #end_time = time.clock()
        """
        n_times = 0
        sum_times = 0
        for t in self.move_times:
            n_times += 1
            sum_times += t

        if n_times > 0:
            gamelib.debug_write("Movement took {}s".format(sum_times))
        else:
            gamelib.debug_write("Movement was not completed")
        
        n_times = 0
        sum_times = 0
        for t in self.attack_times:
            n_times += 1
            sum_times += t

        if n_times > 0:
            gamelib.debug_write("Attacking took {}s".format(sum_times))
        else:
            gamelib.debug_write("Attacking was not completed")

        gamelib.debug_write("Actual simulation took {}s".format(end_time-start_time))
        """
        #self.game_state.game_map.show_board(self.game_state.game_map.TOP_LEFT)

        return self.game_state.game_map.map

    def frame(self):
        """ 
        Order:
        Each unit takes a step, if it is time for them to take a step.
        Each shield decays.
        New shields are applied, if a unit has entered the range of a friendly encryptor
        All units attack.
        Units that were reduced below 0 stability are removed
        """

        self.curr_frame += 1

        #start_time = time.clock()
        self.move_units()
        #end_time = time.clock()
        #self.move_times.append(end_time-start_time)

        if self.finished:
            return

        #start_time = time.clock()
        self.unit_attack()
        #end_time = time.clock()
        #self.attack_times.append(end_time-start_time)


    def move_units(self):
        from .game_state import is_stationary

        game_state = self.game_state
        game_map = game_state.game_map

        removal_list = []

        i=-1

        for unit in self.unit_list:
            i += 1
            unit.decay()

            if self.curr_frame % (1 / unit.speed) == 0:

                if game_state.game_map.pathfinding_map[unit.loc[0]][unit.loc[1]].dist[unit.path_target] == 1 and game_state.game_map.pathfinding_map[unit.loc[0]][unit.loc[1]].temp[unit.path_target]:
                    # Self destruct
                    game_map[unit.x, unit.y].remove(unit)
                    removal_list.append(unit)

                    if unit.tiles_moved >= 5:
                        # Deal damage to enemy units
                        for loc in game_map.get_locations_in_range(unit.loc, 1.5):
                            if game_map.in_arena_bounds(loc):
                                for attacked_unit in game_map[loc]:
                                    if attacked_unit.player_index != unit.player_index and attacked_unit.stability > 0:
                                        attacked_unit.attack(unit.max_stability)

                                        if attacked_unit.stability <= 0:
                                            removal_list.append(attacked_unit)

                    continue
                    
                if unit.loc in game_map.edges[unit.path_target]:
                    if unit.player_index == 0:
                        game_state.enemy_health -= 1
                    else:
                        game_state.my_health -= 1

                    removal_list.append(unit)

                    continue

                unit.tiles_moved += 1

                new_loc = game_map.next_loc(unit)

                if new_loc[0] != unit.x:
                    unit.next_dir_up = True
                elif new_loc[1] != unit.y:
                    unit.next_dir_up = False

                game_map[unit.x, unit.y].remove(unit)

                unit.loc = new_loc
                unit.x = new_loc[0]
                unit.y = new_loc[1]

                game_map[new_loc[0], new_loc[1]].append(unit)

        for unit in removal_list:
            if not is_stationary(unit.unit_type):
                self.unit_list.remove(unit)
            else:
                game_map[unit.loc].pop(0)
                if unit.unit_type == ENCRYPTOR:
                    encryptor_list.remove(unit)
                new_loc = set()
                new_loc.add(gamelib.Coord(unit.loc))
                game_map.propogate_from_set(new_loc)

        if len(self.unit_list) == 0:
            self.finished = True
        

    def unit_attack(self):
        from .game_state import is_stationary

        game_state = self.game_state
        game_map = game_state.game_map

        stationary_list = set()
        stationary_locs = set()
        dead_units = []
        removal_list = []

        loc_in_range = self.loc_in_range
        encryptor_list = self.encryptor_list

        # Go through encryptors
        for encryptor in encryptor_list:
            for loc in loc_in_range:
                loc = [loc[0] + unit.x, loc[1] + unit.y]
                if game_map.in_arena_bounds(loc):
                    if len(game_map[loc]) > 0:
                        if not game_state.contains_stationary_unit(loc):
                            for unit in game_map[loc]:
                                if unit.player_index == encryptor.player_index and unit.id not in encryptor.encrypted_IDs:
                                    unit.encrypt(encryptor.damage)
                                    encryptor.encrypted_IDs.append(unit.id)

        # Go through information units
        #start_time = time.clock()
        for unit in self.unit_list:
            #stationary_list.concatenate(game_map.get_locations_in_range(unit.loc, 3))
            #s_t = time.clock()
            for loc in loc_in_range:
                loc = [loc[0] + unit.x, loc[1] + unit.y]
                if game_map.in_arena_bounds(loc) and game_state.contains_stationary_unit(loc):
                    if game_map[loc][0].player_index != unit.player_index and game_map[loc][0].unit_type != ENCRYPTOR:
                        if game_map[loc][0] not in stationary_list:
                            stationary_list.add(game_map[loc][0])
            #mid_t = time.clock()

            # Attack

            """
            If we didn't move:
            If our target was stationary:
            - We might need to check for pings entering the radius, if this unit is an Emp or a Scrambler
            - If we didn't move, and it still exists, it is likely still our target. In any case, we only have to search the same distance for alternatives
            - If we didn't move and it doesn't exist, we can start our search starting at the same distance that we were from with the last target

            If our target was information:
            - If it still exists, we probably don't have to retarget, but at the very least, we only need to check the same ring
            - If it no longer exists, our search for information units can start at the same distance, but the search for stationary units is unchanged

            If we didn't have a target:
            We can search the outer rim, and leave it at that


            If we did move:
            If our target was stationary:
            - Our search for information units can be at the limit of the radius-1
            - Our search for stationary units can be starting at the target at the last frame-1

            If our target was information:
            - Our search for information units starts at the distance last frame-2
            - Our search for stationary units starts from the beginning

            If we didn't have a target:
            We can limit the search to radius-1


            What we need to do to get_target:
            - Limit search for information units to starting at a certain radius
            - Limit search for stationary units starting at certain location
            - Save distance from target last time
            """
            
            info_start = 0
            fire_start = 0

            # Starting info and fire ranges
            if unit.target == None:
                info_start = unit.range+1
                fire_start = unit.range+1
            else:
                if is_stationary(unit.target.unit_type):
                    info_start = unit.range+1
                    fire_start = unit.d_target
                else:
                    info_start = unit.d_target
                    fire_start = 0


            # Modify info and fire ranges

            # If we moved, subtract 1 because we could have moved closer to units
            if self.curr_frame % (1 / unit.speed) == 0:
                info_start -= 1
                fire_start -= 1

            # If information units could have moved, subtract one because they could be closer
            if self.curr_frame % 2 == 0:
                info_start -= 1
            
            if info_start < unit.range or fire_start < unit.range:
                target = game_state.get_target(unit, info_start, fire_start)
            else:
                target = None
            
            #target = game_state.get_target(unit)
            #timme = time.clock()
            #target = game_state.get_target(unit, 5, 5)
            #gamelib.debug_write("Finding target took {}s".format(time.clock()-timme))

            if target != None:
                target.attack(unit.damage)
                unit.d_target = game_map.distance_between_locations(unit.loc, target.loc)

                if target.stability <= 0:
                    removal_list.append(target)
            else:
                unit.d_target = 0
                unit.target = None
            #e_t = time.clock()

            #gamelib.debug_write("Time for adding stationary: {}".format(mid_t-s_t))
            #gamelib.debug_write("Time for finding a target: {}".format(e_t-mid_t))

        #end_time = time.clock()
        #gamelib.debug_write("Time for information units: {}".format(end_time-start_time))

        # Go through stationary units that might do something
        #start_time = time.clock()
        for unit in stationary_list:

            info_start = 0
            fire_start = 4
            
            # We didn't move, so certain optimizations can be made
            if unit.target == None:
                info_start = unit.range
            elif self.curr_frame % 2 == 0:
                info_start = unit.d_target-1
            else:
                info_start = unit.d_target

            # Attack
            target = game_state.get_target(unit, info_start, fire_start)

            if target != None:
                target.attack(unit.damage)

                if target.stability <= 0:
                    removal_list.append(target)

        #end_time = time.clock()
        #gamelib.debug_write("Time for stationary units: {}".format(end_time-start_time))
        """
        for stationary_loc in stationary_locs:
            if game_map.in_arena_bounds(stationary_loc) and game_state.contains_stationary_unit(loc):
                unit = game_map[stationary_loc][0]
                target = game_state.get_target(unit)

                if target != None:
                    target.attack(unit.damage)
                    removal_list.append(target)
        """
        for unit in removal_list:
            if not is_stationary(unit.unit_type):
                self.unit_list.remove(unit)
                game_map[unit.x, unit.y].remove(unit)
            else:
                game_map[unit.loc].pop(0)
                #gamelib.debug_write("Hey we actually destroyed a unit yay")
                if unit.unit_type == ENCRYPTOR:
                    encryptor_list.remove(unit)
                #gamelib.debug_write("Unit destroyed, re-pathing. Frame = {}, loc = {}".format(self.curr_frame, unit.loc))
                new_loc = set()
                new_loc.add(gamelib.Coord(unit.loc))
                game_map.propogate_from_set(new_loc)
                #gamelib.debug_write("Done re-pathing")
                    
        if len(self.unit_list) == 0:
            self.finished = True

    def idealness(self):
        cores_on_board = [0, 0]
        cores_in_storage = [self.game_state.get_resource(self.game_state.CORES, 0), self.game_state.get_resource(self.game_state.CORES, 1)] # This can be set now
        bits_in_storage = [self.game_state.get_resource(self.game_state.BITS, 0), self.game_state.get_resource(self.game_state.CORES, 1)] # This can be set now
        player_health = [self.game_state.my_health, self.game_state.enemy_health]

        cores_on_board_weight = 0.75
        cores_in_storage_weight = 1
        bits_in_storage_weight = 0.5
        player_health_weight = 2

        overall_score = [0, 0]


        for x in range(0, self.game_state.game_map.ARENA_SIZE):
            for y in range(0, self.game_state.game_map.ARENA_SIZE):
                if self.game_state.game_map.in_arena_bounds([x, y]):
                    if self.game_state.contains_stationary_unit([x, y]):
                        cores_on_board[self.game_state.game_map[x, y][0].player_index] += self.game_state.game_map[x, y][0].cost

        for i in range(0, 2):
            overall_score[i] += cores_on_board[i] * cores_on_board_weight
            overall_score[i] += cores_in_storage[i] * cores_in_storage_weight
            overall_score[i] += bits_in_storage[i] * bits_in_storage_weight
            overall_score[i] += player_health[i] * player_health_weight

        return overall_score[0] - overall_score[1]



class Storage:
    def __init__(self, config):

        self.config = config
        self.ARENA_SIZE = 28
        self.HALF_ARENA = int(self.ARENA_SIZE / 2)
        self.TOP_RIGHT = 0
        self.TOP_LEFT = 1
        self.BOTTOM_LEFT = 2
        self.BOTTOM_RIGHT = 3

        self.arena_bounds = []

        self.list = []
        for x in range(0, 1001):
            self.list.append(x)
            if x == 1000:
                self.list[x] == -1

        self.locs_in_range_1 = self.__get_locations_in_range([0,0], 1.5)
        self.locs_in_range_3 = self.__get_locations_in_range([0,0], 3)
        self.locs_in_range_5 = self.__get_locations_in_range([0,0], 5)
        self.split_locs_3 = self.__parse_locs(self.locs_in_range_3)
        self.split_locs_5 = self.__parse_locs(self.locs_in_range_5)

        self.edges = self.__get_edges()
        
        for x in range(0, 28+5):

            self.arena_bounds.append([])

            for y in range(0, 28+5):

                if x >= 28 or y >= 28:
                    self.arena_bounds[x].append(False)

                else:
                    
                    half_board = self.HALF_ARENA

                    row_size = y + 1
                    startx = half_board - row_size
                    endx = startx + (2 * row_size) - 1
                    top_half_check = (y < self.HALF_ARENA and x >= startx and x <= endx)

                    row_size = (self.ARENA_SIZE - 1 - y) + 1
                    startx = half_board - row_size
                    endx = startx + (2 * row_size) - 1
                    bottom_half_check = (y >= self.HALF_ARENA and x >= startx and x <= endx)

                    self.arena_bounds[x].append(bottom_half_check or top_half_check)


    def in_arena_bounds(self, loc):
        #x, y = loc
        #return self.arena_bounds[x][y]
        return self.arena_bounds[loc[0]][loc[1]]
        #x, y = loc
        #if x >= 28 or x < 0 or y >= 28 or y < 0:
        #    return False
        #else:
        #    return self.arena_bounds[x][y]
        

    def __get_locations_in_range(self, location, radius):
        
        x, y = location
        locations = []

        for i in range(int(x - radius), int(x + radius + 1)):
            for j in range(int(y - radius), int(y + radius + 1)):
                new_location = [i, j]

                # A unit with a given range affects all locations who's centers are within that range + 0.51 so we add 0.51 here
                if self.distance_between_locations(location, new_location) < radius + 0.51:
                    locations.append(new_location)


        return sorted(locations, reverse=False, key=self.distance_between_locations)

    def __parse_locs(self, sorted_locations):
        curr_lowest = -1
        locs = []
        index = -1

        for loc in sorted_locations:
            if self.distance_between_locations(loc) > curr_lowest:
                index += 1
                curr_lowest = self.distance_between_locations([0,0], loc)
                locs.append([])
            locs[index].append(loc)

        for this_set in locs:
            gamelib.debug_write("Distance: {}.  Set: {}".format(self.distance_between_locations(this_set[0]), this_set))

        return locs


    def __get_edges(self):
        """Gets all of the edges and their edge locations

        Returns:
            A list with four lists inside of it of locations corresponding to the four edges.
            [0] = top_right, [1] = top_left, [2] = bottom_left, [3] = bottom_right.
        """
        top_right = []
        for num in range(0, self.HALF_ARENA):
            x = self.HALF_ARENA + num
            y = self.ARENA_SIZE - 1 - num
            top_right.append([int(x), int(y)])
        top_left = []
        for num in range(0, self.HALF_ARENA):
            x = self.HALF_ARENA - 1 - num
            y = self.ARENA_SIZE - 1 - num
            top_left.append([int(x), int(y)])
        bottom_left = []
        for num in range(0, self.HALF_ARENA):
            x = self.HALF_ARENA - 1 - num
            y = num
            bottom_left.append([int(x), int(y)])
        bottom_right = []
        for num in range(0, self.HALF_ARENA):
            x = self.HALF_ARENA + num
            y = num
            bottom_right.append([int(x), int(y)])
        return [top_right, top_left, bottom_left, bottom_right]


    def distance_between_locations(self, location_1, location_2=[0,0]):
        """Euclidean distance

        Args:
            * location_1: An arbitrary location
            * location_2: An arbitrary location

        Returns:
            The euclidean distance between the two locations

        """
        x1, y1 = location_1
        x2, y2 = location_2

        return math.sqrt((x1 - x2)**2 + (y1 - y2)**2)



class Possible_Attack:
    def __init__(self, unit_type, location, idealness):
        self.unit_type = unit_type
        self.location = location
        self.idealness = idealness


        
class Simulator_2:
    def __init__(self, config, serialized_string, storage):
        
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, REMOVE, FIREWALL_TYPES, ALL_UNITS, UNIT_TYPE_TO_INDEX
        UNIT_TYPE_TO_INDEX = {}
        FILTER = config["unitInformation"][0]["shorthand"]
        UNIT_TYPE_TO_INDEX[FILTER] = 0
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        UNIT_TYPE_TO_INDEX[ENCRYPTOR] = 1
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        UNIT_TYPE_TO_INDEX[DESTRUCTOR] = 2
        PING = config["unitInformation"][3]["shorthand"]
        UNIT_TYPE_TO_INDEX[PING] = 3
        EMP = config["unitInformation"][4]["shorthand"]
        UNIT_TYPE_TO_INDEX[EMP] = 4
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        UNIT_TYPE_TO_INDEX[SCRAMBLER] = 5
        REMOVE = config["unitInformation"][6]["shorthand"]
        UNIT_TYPE_TO_INDEX[REMOVE] = 6

        ALL_UNITS = [PING, EMP, SCRAMBLER, FILTER, ENCRYPTOR, DESTRUCTOR]
        FIREWALL_TYPES = [FILTER, ENCRYPTOR, DESTRUCTOR]

        self.config = config
        self.game_state = gamelib.AdvancedGameState(config, serialized_string, storage, True)
        self.finished = False
        self.curr_frame = 0

        self.move_times = []
        self.attack_times = []

        self.unit_list = set()
        self.encryptor_list = set()

        self.loc_in_range = self.game_state.game_map.get_locations_in_range([0,0], 3, True)
        self.loc_in_range_1 = self.game_state.game_map.get_locations_in_range([0,0], 1, True)

        self.calculated = False


    def calculate(self):
        self.game_state.game_map.calculate()
        self.calculated = True


    def simulate(self):
        #gamelib.debug_write("New simulation")

        if not self.calculated:
            self.game_state.game_map.calculate()

        #self.game_state.game_map.show_board(self.game_state.game_map.TOP_LEFT)

        for x in range(0, self.game_state.game_map.ARENA_SIZE):
            for y in range(0, self.game_state.game_map.ARENA_SIZE):
                if self.game_state.game_map.in_arena_bounds([x,y]):
                    if not self.game_state.contains_stationary_unit([x,y]) and len(self.game_state.game_map[x,y]) >= 1:
                        for unit in self.game_state.game_map[x,y]:
                            self.unit_list.add(unit)
                    elif len(self.game_state.game_map[x,y]) == 1 and self.game_state.game_map[x,y][0].unit_type == ENCRYPTOR:
                        self.encryptor_list.add(self.game_state.game_map[x,y][0])
        #gamelib.debug_write("Finished making simulation lists. Turn = {}".format(self.game_state.turn_number))
        #timeit self.frame()

        #start_time = time.clock()
        while not self.finished:
            self.frame()
        #end_time = time.clock()
        """
        n_times = 0
        sum_times = 0
        for t in self.move_times:
            n_times += 1
            sum_times += t

        if n_times > 0:
            gamelib.debug_write("Movement took {}s".format(sum_times))
        else:
            gamelib.debug_write("Movement was not completed")
        
        n_times = 0
        sum_times = 0
        for t in self.attack_times:
            n_times += 1
            sum_times += t

        if n_times > 0:
            gamelib.debug_write("Attacking took {}s".format(sum_times))
        else:
            gamelib.debug_write("Attacking was not completed")

        gamelib.debug_write("Actual simulation took {}s".format(end_time-start_time))
        """
        #self.game_state.game_map.show_board(self.game_state.game_map.TOP_LEFT)

        return self.game_state.game_map.map

    def frame(self):
        """ 
        Order:
        Each unit takes a step, if it is time for them to take a step.
        Each shield decays.
        New shields are applied, if a unit has entered the range of a friendly encryptor
        All units attack.
        Units that were reduced below 0 stability are removed
        """

        self.curr_frame += 1

        #start_time = time.clock()
        self.move_units()
        #end_time = time.clock()
        #self.move_times.append(end_time-start_time)

        if self.finished:
            return

        #start_time = time.clock()
        self.unit_attack()
        #end_time = time.clock()
        #self.attack_times.append(end_time-start_time)


    def move_units(self):
        from .game_state import is_stationary

        game_state = self.game_state
        game_map = game_state.game_map

        removal_list = []

        i=-1

        for unit in self.unit_list:
            i += 1
            unit.decay()

            if self.curr_frame % (1 / unit.speed) == 0:

                if game_state.game_map.pathfinding_map[unit.loc[0]][unit.loc[1]].dist[unit.path_target] == 1 and game_state.game_map.pathfinding_map[unit.loc[0]][unit.loc[1]].temp[unit.path_target]:
                    # Self destruct
                    game_map[unit.x, unit.y].remove(unit)
                    removal_list.append(unit)

                    if unit.tiles_moved >= 5:
                        # Deal damage to enemy units
                        for loc in game_map.get_locations_in_range(unit.loc, 1.5):
                            if game_map.in_arena_bounds(loc):
                                for attacked_unit in game_map[loc]:
                                    if attacked_unit.player_index != unit.player_index:
                                        attacked_unit.attack(unit.max_stability)

                                        if attacked_unit.stability <= 0:
                                            removal_list.append(attacked_unit)

                    continue
                    
                if unit.loc in game_map.edges[unit.path_target]:
                    if unit.player_index == 0:
                        game_state.enemy_health -= 1
                    else:
                        game_state.my_health -= 1

                    removal_list.append(unit)

                    continue

                unit.tiles_moved += 1

                new_loc = game_map.next_loc(unit)

                if new_loc[0] != unit.x:
                    unit.next_dir_up = True
                elif new_loc[1] != unit.y:
                    unit.next_dir_up = False

                game_map[unit.x, unit.y].remove(unit)

                unit.loc = new_loc
                unit.x = new_loc[0]
                unit.y = new_loc[1]

                game_map[new_loc[0], new_loc[1]].append(unit)

        for unit in removal_list:
            if not is_stationary(unit.unit_type):
                self.unit_list.remove(unit)
            else:
                game_map[unit.loc].pop(0)
                if unit.unit_type == ENCRYPTOR:
                    encryptor_list.remove(unit)
                new_loc = set()
                new_loc.add(gamelib.Coord(unit.loc))
                game_map.propogate_from_set(new_loc)

        if len(self.unit_list) == 0:
            self.finished = True
        

    def unit_attack(self):
        from .game_state import is_stationary

        game_state = self.game_state
        game_map = game_state.game_map

        stationary_list = set()
        stationary_locs = set()
        dead_units = []
        removal_list = []

        loc_in_range = self.loc_in_range
        encryptor_list = self.encryptor_list

        # Go through encryptors
        for encryptor in encryptor_list:
            for loc in loc_in_range:
                loc = [loc[0] + unit.x, loc[1] + unit.y]
                if game_map.in_arena_bounds(loc):
                    if len(game_map[loc]) > 0:
                        if not game_state.contains_stationary_unit(loc):
                            for unit in game_map[loc]:
                                if unit.player_index == encryptor.player_index and unit.id not in encryptor.encrypted_IDs:
                                    unit.encrypt(encryptor.damage)
                                    encryptor.encrypted_IDs.append(unit.id)

        # Go through information units
        #start_time = time.clock()
        for unit in self.unit_list:
            #stationary_list.concatenate(game_map.get_locations_in_range(unit.loc, 3))
            #s_t = time.clock()
            for loc in loc_in_range:
                loc = [loc[0] + unit.x, loc[1] + unit.y]
                if game_map.in_arena_bounds(loc) and game_state.contains_stationary_unit(loc):
                    if game_map[loc][0].player_index != unit.player_index and game_map[loc][0].unit_type != ENCRYPTOR:
                        if game_map[loc][0] not in stationary_list:
                            stationary_list.add(game_map[loc][0])
            #mid_t = time.clock()

            # Attack

            """
            If we didn't move:
            If our target was stationary:
            - We might need to check for pings entering the radius, if this unit is an Emp or a Scrambler
            - If we didn't move, and it still exists, it is likely still our target. In any case, we only have to search the same distance for alternatives
            - If we didn't move and it doesn't exist, we can start our search starting at the same distance that we were from with the last target

            If our target was information:
            - If it still exists, we probably don't have to retarget, but at the very least, we only need to check the same ring
            - If it no longer exists, our search for information units can start at the same distance, but the search for stationary units is unchanged

            If we didn't have a target:
            We can search the outer rim, and leave it at that


            If we did move:
            If our target was stationary:
            - Our search for information units can be at the limit of the radius-1
            - Our search for stationary units can be starting at the target at the last frame-1

            If our target was information:
            - Our search for information units starts at the distance last frame-2
            - Our search for stationary units starts from the beginning

            If we didn't have a target:
            We can limit the search to radius-1


            What we need to do to get_target:
            - Limit search for information units to starting at a certain radius
            - Limit search for stationary units starting at certain location
            - Save distance from target last time
            """
            
            info_start = 0
            fire_start = 0

            # Starting info and fire ranges
            if unit.target == None:
                info_start = unit.range+1
                fire_start = unit.range+1
            else:
                if is_stationary(unit.target.unit_type):
                    info_start = unit.range+1
                    fire_start = unit.d_target
                else:
                    info_start = unit.d_target
                    fire_start = 0


            # Modify info and fire ranges

            # If we moved, subtract 1 because we could have moved closer to units
            if self.curr_frame % (1 / unit.speed) == 0:
                info_start -= 1
                fire_start -= 1

            # If information units could have moved, subtract one because they could be closer
            if self.curr_frame % 2 == 0:
                info_start -= 1
            
            if info_start < unit.range or fire_start < unit.range:
                target = game_state.get_target_2(unit, info_start, fire_start)
            else:
                target = None
            
            #target = game_state.get_target(unit)
            #timme = time.clock()
            #target = game_state.get_target(unit, 5, 5)
            #gamelib.debug_write("Finding target took {}s".format(time.clock()-timme))

            if target != None:
                target.attack(unit.damage)
                unit.d_target = game_map.distance_between_locations(unit.loc, target.loc)

                if target.stability <= 0:
                    removal_list.append(target)
            else:
                unit.d_target = 0
                unit.target = None
            #e_t = time.clock()

            #gamelib.debug_write("Time for adding stationary: {}".format(mid_t-s_t))
            #gamelib.debug_write("Time for finding a target: {}".format(e_t-mid_t))

        #end_time = time.clock()
        #gamelib.debug_write("Time for information units: {}".format(end_time-start_time))

        # Go through stationary units that might do something
        #start_time = time.clock()
        for unit in stationary_list:

            info_start = 0
            fire_start = 4
            
            # We didn't move, so certain optimizations can be made
            if unit.target == None:
                info_start = unit.range
            elif self.curr_frame % 2 == 0:
                info_start = unit.d_target-1
            else:
                info_start = unit.d_target

            # Attack
            target = game_state.get_target(unit, info_start, fire_start)

            if target != None:
                target.attack(unit.damage)

                if target.stability <= 0:
                    removal_list.append(target)

        #end_time = time.clock()
        #gamelib.debug_write("Time for stationary units: {}".format(end_time-start_time))
        """
        for stationary_loc in stationary_locs:
            if game_map.in_arena_bounds(stationary_loc) and game_state.contains_stationary_unit(loc):
                unit = game_map[stationary_loc][0]
                target = game_state.get_target(unit)

                if target != None:
                    target.attack(unit.damage)
                    removal_list.append(target)
        """
        for unit in removal_list:
            if not is_stationary(unit.unit_type):
                self.unit_list.remove(unit)
                game_map[unit.x, unit.y].remove(unit)
            else:
                game_map[unit.loc].pop(0)
                #gamelib.debug_write("Hey we actually destroyed a unit yay")
                if unit.unit_type == ENCRYPTOR:
                    encryptor_list.remove(unit)
                #gamelib.debug_write("Unit destroyed, re-pathing. Frame = {}, loc = {}".format(self.curr_frame, unit.loc))
                new_loc = set()
                new_loc.add(gamelib.Coord(unit.loc))
                game_map.propogate_from_set(new_loc)
                #gamelib.debug_write("Done re-pathing")
                    
        if len(self.unit_list) == 0:
            self.finished = True

    def idealness(self):
        cores_on_board = [0, 0]
        cores_in_storage = [self.game_state.get_resource(self.game_state.CORES, 0), self.game_state.get_resource(self.game_state.CORES, 1)] # This can be set now
        bits_in_storage = [self.game_state.get_resource(self.game_state.BITS, 0), self.game_state.get_resource(self.game_state.CORES, 1)] # This can be set now
        player_health = [self.game_state.my_health, self.game_state.enemy_health]

        cores_on_board_weight = 0.75
        cores_in_storage_weight = 1
        bits_in_storage_weight = 0.5
        player_health_weight = 2

        overall_score = [0, 0]


        for x in range(0, self.game_state.game_map.ARENA_SIZE):
            for y in range(0, self.game_state.game_map.ARENA_SIZE):
                if self.game_state.game_map.in_arena_bounds([x, y]):
                    if self.game_state.contains_stationary_unit([x, y]):
                        cores_on_board[self.game_state.game_map[x, y][0].player_index] += self.game_state.game_map[x, y][0].cost

        for i in range(0, 2):
            overall_score[i] += cores_on_board[i] * cores_on_board_weight
            overall_score[i] += cores_in_storage[i] * cores_in_storage_weight
            overall_score[i] += bits_in_storage[i] * bits_in_storage_weight
            overall_score[i] += player_health[i] * player_health_weight

        return overall_score[0] - overall_score[1]

