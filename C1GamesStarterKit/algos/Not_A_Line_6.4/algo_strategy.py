import gamelib
import random
import math
from math import sqrt
import warnings
import json
import operator
from sys import maxsize

"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

Additional functions are made available by importing the AdvancedGameState 
class from gamelib/advanced.py as a replcement for the regular GameState class 
in game.py.

You can analyze action frames by modifying algocore.py.

The GameState.map object can be manually manipulated to create hypothetical 
board states. Though, we recommended making a copy of the map to preserve 
the actual current map state.
"""

class AlgoStrategy(gamelib.AlgoCore):

    def __init__(self):
        super().__init__()
        random.seed()

    def on_game_start(self, config,game_state_string):

        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        self.game_state_string = game_state_string
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

        ALL_UNITS = [PING, EMP, SCRAMBLER, FILTER, ENCRYPTOR, DESTRUCTOR]
        FIREWALL_TYPES = [FILTER, ENCRYPTOR, DESTRUCTOR]
        self.ARENA_SIZE = 28
        self.HALF_ARENA = int(self.ARENA_SIZE / 2)
        
        self.lastAttack = 0
        self.EMP = 0
        self.PING = 1
        self.ideal_map = gamelib.GameMap(config)

        self.action_phase = False
        self.units_sent = False
        self.emp_spawn_locs = [[14, 0],[13, 0]]
        self.emp_spawn_loc = []

        self.self_movement_map = []
        self.self_movement_path = []
        self.information_attacked_flags = []

        self.enemy_spawn_locs = []
        self.enemy_movement_map = []
        self.enemy_movement_path = []
        self.enemy_attack_map = []

        self.destructor_locations = [[ 2, 11],[ 7, 11],[ 11, 11],[ 16, 11],[ 20, 11],[ 25, 11],[ 3, 10],[ 24, 10],[ 5, 8],[ 9, 8],[ 13, 8],[ 14, 8],[ 18, 8],[ 22, 8],[ 6, 7],[ 21, 7]]
        self.filter_locations = [[ 0, 13],[ 27, 13],[ 1, 12],[ 2, 12],[ 7, 12],[ 11, 12],[ 16, 12],[ 20, 12],[ 25, 12],[ 26, 12],[ 3, 11],[ 6, 11],[ 8, 11],[ 10, 11],[ 12, 11],[ 15, 11],[ 17, 11],[ 19, 11],[ 21, 11],[ 24, 11],[ 4, 10],[ 23, 10],[ 5, 9],[ 9, 9],[ 13, 9],[ 14, 9],[ 18, 9],[ 22, 9],[ 6, 8],[ 8, 8],[ 10, 8],[ 12, 8],[ 15, 8],[ 17, 8],[ 19, 8],[ 21, 8]]
        self.encryptor_locations = [[ 4, 9],[ 23, 9],[ 9, 7],[ 10, 7],[ 17, 7],[ 18, 7],[ 7, 6],[ 9, 6],[ 10, 6],[ 11, 6],[ 12, 6],[ 15, 6],[ 16, 6],[ 17, 6],[ 18, 6],[ 20, 6],[ 10, 5],[ 11, 5],[ 12, 5],[ 15, 5],[ 16, 5],[ 17, 5],[ 11, 4],[ 12, 4],[ 15, 4],[ 16, 4],[ 12, 3],[ 15, 3]]

        self.build_sets = []

        for loc in self.destructor_locations:
            self.ideal_map.add_unit(DESTRUCTOR, loc, 0)
            build_list = [Build(DESTRUCTOR, loc, 0)]

            for filter in self.filter_locations:
                if self.ideal_map.distance_between_locations(loc, filter) == 1 or (self.ideal_map.distance_between_locations(loc, filter) == sqrt(2) and (loc == [2,11] or loc == [25,11])) or (loc == [25, 11] and filter == [27, 13]) or (loc == [2, 11] and filter == [0, 13]):

                    if len(self.ideal_map[filter]) == 0:
                        build_list.append(Build(FILTER, filter, 0))
                        self.ideal_map.add_unit(FILTER, filter, 0)
                    else:
                        gamelib.debug_write("Tried to add filters to multiple locations at point ({}, {})".format(filter[0], filter[1]))

            self.build_sets.append(BuildSet(build_list, 0, 0))


        #for loc in self.filter_locations:
        #    self.ideal_map.add_unit(FILTER, loc, 0)

        for loc in self.encryptor_locations:
            self.ideal_map.add_unit(ENCRYPTOR, loc, 0)
            self.build_sets.append(BuildSet([Build(ENCRYPTOR, loc, 0)], 0, 4.0))

        for build_set in self.build_sets:
            gamelib.debug_write("New build list made up of:")
            for build in build_set.build_list:
                gamelib.debug_write("A {} at ({}, {})  ".format(build.unit_type, build.loc[0], build.loc[1]))


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        if self.action_phase:
            self.action_phase = False

        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Uncomment this line to suppress warnings.
        self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def starter_strategy(self, game_state):
        self.build_base_defences(game_state)
        
        self.deploy_attackers(game_state)

        self.emp_path = []

    # Here we make the base defences!
    def build_base_defences(self, game_state):
        # Calculate probability of building
        necessary_sets = []
        emp_paths = []
        emp_path = []
        for spawn_loc in self.emp_spawn_locs:
            temp_emp_path = game_state.find_path_to_edge(spawn_loc)
            if emp_path == [] or len(temp_emp_path) < len(emp_path) or (len(temp_emp_path) == len(emp_path) and temp_emp_path[-1][1] < emp_path[-1][1]):
                emp_path = temp_emp_path
                self.emp_spawn_loc = spawn_loc


        for build_set in self.build_sets:
            build_set.probability = 0
            necessary = False
            build_set.cost = 0
            n_missing = 0
            any_built = False

            for build in build_set.build_list:
                build.probability = 0

                if game_state.contains_stationary_unit(build.loc):
                    build.probability = -1
                    if game_state.game_map[build.loc][0].stability < game_state.game_map[build.loc][0].max_stability/2:
                        game_state.attempt_remove(build.loc)
                    if not any_built:
                        any_built = True

                else:
                    if build.unit_type == FILTER:
                        enemy_attack_filter_loc = 0
                        enemy_attack_destructor_loc = 0
                        if len(self.enemy_attack_map) > 0:
                            for i in range(1, min(3, len(self.enemy_attack_map))):
                                enemy_attack_filter_loc += self.enemy_attack_map[-i][build.loc[0]][build.loc[1]]
                                enemy_attack_destructor_loc += self.enemy_attack_map[-i][build_set.build_list[0].loc[0]][build_set.build_list[0].loc[1]]
                        
                        if enemy_attack_filter_loc > 0 and enemy_attack_destructor_loc == 0:
                            build.probability = -1
                            gamelib.debug_write("Not flagging filter for rebuilding at location ({}, {}) because it would just be destroyed".format(build.loc[0], build.loc[1]))
                        else:
                            build_set.cost += 1
                            n_missing += 1
                            if game_state.contains_stationary_unit(build_set.build_list[0].loc):
                                build_set.probability += enemy_attack_destructor_loc


                    elif build.unit_type == DESTRUCTOR:
                        # Check to what extent we attack where they are moving
                        n_attack_locs = 0
                        n_missing += 1

                        if game_state.turn_number == 0:
                            if build.loc[1] == 8 and build.loc[0] != 5 and build.loc[0] != 22:
                                build_set.probability = 100
                        
                        if len(self.enemy_movement_map) > 0:
                            for loc in self.ideal_map.get_locations_in_range(build.loc, 3.0):
                                for i in range(1, min(3, len(self.enemy_movement_map) + 1)):
                                    if self.enemy_movement_map[-i][loc[0]][loc[1]] > 0:
                                        n_attack_locs += 1
                                        continue
                                    
                        build_set.probability += n_attack_locs * 1.0

                        build_set.cost += 3
                        
                    elif build.unit_type == ENCRYPTOR:
                        #build_set.probability += 0.00001

                        n_missing += 1
                        closeness_score = 0
                        closeness_score_2 = 0
                        emp_iter_2 = -1
                        emp_iter_3 = -1
                        ping_iter = -1
                        curr_index = len(emp_path)

                        if len(self.information_attacked_flags) > 0:
                            for i in reversed(range(1, min(3, len(self.information_attacked_flags)))):
                                if len(self.information_attacked_flags[-i]) > 0:
                                    emp_iter_2 = len(self.information_attacked_flags[-i])
                                    for loc in reversed(self.self_movement_path[-i]):
                                        emp_iter_2 -=1
                                        if loc == self.self_movement_path[-i]:
                                            emp_iter_3 = emp_iter_2
                                        if loc[1] == 10:
                                            closeness_score_2 = 4 - self.ideal_map.distance_between_locations(loc, build.loc)
                                            break
                
                        for loc in self.ideal_map.get_locations_in_range(build.loc, 3.0):
                            
                            if loc in emp_path:
                                if ping_iter == -1 or ping_iter > emp_path.index(loc):
                                    ping_iter = emp_path.index(loc)

                            emp_iter = -1
                            attacked_loc = False

                            try:
                                emp_iter = emp_path.index(loc)
                            except:
                                pass

                            if emp_iter >= 0 and len(self.enemy_attack_map) > 0:
                                for i in range(1, min(3, len(self.enemy_attack_map))):
                                    if self.enemy_attack_map[-i][loc[0]][loc[1]] > 0:
                                        attacked_loc = True
                                        break

                                if attacked_loc and emp_iter < curr_index:
                                    closeness_score = 4 - self.ideal_map.distance_between_locations(emp_path[emp_iter], build.loc)

                        if closeness_score > 0:
                            build_set.probability += closeness_score * 0.4 + (len(emp_path)*2 - emp_iter) / (len(emp_path)*20)
                            
                        if closeness_score_2 > 0:
                            build_set.probability += closeness_score_2 * 0.4 * ((10.0 / 1.5) - (emp_iter_3 - emp_iter_2)) / (10.0 / 1.5)

                        if ping_iter != -1:
                            build_set.probability += ping_iter / 50

                        build_set.cost += 4
                    """
                    emp_path_iter = -1
                    try:
                        emp_path_iter = emp_path.index(build.loc)
                    except:
                        pass

                    if emp_path_iter >= 0:
                        build_set.probability += (len(emp_path)*2 - emp_path_iter) / (len(emp_path)*2) / 20
                    """
            if n_missing > 0:
                necessary_sets.append(build_set)
                if any_built:
                    build_set.probability += 2

        necessary_sets.sort(key=operator.attrgetter('probability'), reverse=True)
        #random.shuffle(necessary_sets)
        
        for build_set in necessary_sets:
            if game_state.get_resource(game_state.CORES) < build_set.cost or (build_set.probability == 0 and game_state.get_resource(game_state.CORES) < 10):
                return
            gamelib.debug_write("Building a set with probability {} at location".format(build_set.probability))
            for build in build_set.build_list:
                if build.probability >= 0:
                    gamelib.debug_write("({}, {})".format(build.loc[0], build.loc[1]))
                    game_state.attempt_spawn(build.unit_type, build.loc)
                else:
                    gamelib.debug_write("({}, {}), except probability < 0".format(build.loc[0], build.loc[1]))
        

    def deploy_attackers(self, game_state):
        # Do we want to send scramblers?
        sendScramblers = False

        if sendScramblers:
            if game_state.get_resource(game_state.BITS) >= 7:
                nEMP = int((game_state.BITS-1) / 3)
                game_state.attempt_spawn(EMP, self.emp_spawn_loc, nEMP)
                game_state.attempt_spawn(SCRAMBLER, self.emp_spawn_loc, game_state.number_affordable(SCRAMBLER))
                self.units_sent = True
            else:
                self.units_sent = False

        else:
            #if(game_state.number_affordable(EMP) >= 2):
            #    game_state.attempt_spawn(EMP, self.emp_spawn_loc, game_state.number_affordable(EMP))
            #    self.units_sent = True
            bits_necessary = 8 + game_state.turn_number/5


            if game_state.number_affordable(PING) >= 8:
                game_state.attempt_spawn(PING, self.emp_spawn_loc, game_state.number_affordable(PING))
            else:
                self.units_sent = False


        """
        First lets check if we have 10 bits, if we don't we lets wait for 
        a turn where we do.
        """
        """
        if (game_state.get_resource(game_state.BITS) < 10 + int(self.round/5) or (not game_state.contains_stationary_unit([19, 8])) or (not game_state.contains_stationary_unit([21, 9]))):
            return

        if(self.lastAttack == self.EMP):
            game_state.attempt_spawn(PING, [22, 8], int(game_state.get_resource(game_state.BITS)))
            self.lastAttack = self.PING
            return
        
        self.lastAttack = self.EMP
        """ 
        """
        First lets deploy an EMP long range unit to destroy firewalls for us.
        """
        """
        nEMP = 3
        nSCRAMBLER = 1.0

        while(True):
            if(game_state.get_resource(game_state.BITS) >= nEMP*game_state.type_cost(EMP) + int(nSCRAMBLER)*game_state.type_cost(SCRAMBLER) + 3):
                nEMP += 1
            if(game_state.get_resource(game_state.BITS) >= nEMP*game_state.type_cost(EMP) + int(nSCRAMBLER)*game_state.type_cost(SCRAMBLER) + 1):
                nSCRAMBLER += 0.5
            else:
                break
        

        if game_state.can_spawn(EMP, [23, 9], nEMP):
            game_state.attempt_spawn(EMP, [23, 9], nEMP)
            

        while game_state.get_resource(game_state.BITS) >= game_state.type_cost(SCRAMBLER):
            game_state.attempt_spawn(SCRAMBLER, [22,8])
"""

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


    def parse_action_phase(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state)

        any_enemies = False

        for unit in game_state.units:
            if unit.player_index == 1:
                any_enemies = True
                break

        if not any_enemies:
            return

        # Create new locations for the stored information
        if not self.action_phase:
            self.enemy_spawn_locs.append([])

            self.enemy_attack_map.append([])
            for x in range(0, self.ARENA_SIZE):
                self.enemy_attack_map[-1].append([])
                for _ in range(0, self.ARENA_SIZE):
                    self.enemy_attack_map[-1][x].append(0)

            self.enemy_movement_map.append([])
            for x in range(0, self.ARENA_SIZE):
                self.enemy_movement_map[-1].append([])
                for _ in range(0, self.ARENA_SIZE):
                    self.enemy_movement_map[-1][x].append(0)

            if self.units_sent:
                self.self_movement_path.append([])
                self.information_attacked_flags.append([])
                self.self_movement_map.append([])
                for x in range(0, self.ARENA_SIZE):
                    self.self_movement_map[-1].append([])
                    for _ in range(0, self.ARENA_SIZE):
                        self.self_movement_map[-1][x].append(0)

        for unit in game_state.units:
            if unit.player_index == 1:
                # Enemy spawn locations
                if not self.action_phase:
                    if(unit.player_index == 1 and [unit.x, unit.y] not in self.enemy_spawn_locs[-1]):
                        self.enemy_spawn_locs[-1].append([unit.x, unit.y])
                
                # Enemy movement locations
                self.enemy_movement_map[-1][unit.x][unit.y] += 1

                # Enemy movement path (ignored for now)

                # Enemy attack locations (single map)
                for loc in game_state.game_map.get_locations_in_range([unit.x, unit.y], unit.range):
                    self.enemy_attack_map[-1][loc[0]][loc[1]] += 1

                # Enemy attack locations (pathing) (ignored for now)

            elif self.units_sent:
                # Own movement locations
                self.self_movement_map[-1][unit.x][unit.y] += 1
                self.self_movement_path[-1].append([unit.x, unit.y])

                # Check for enemy information units attacking this location
                if unit.y > 10 and len(self.information_attacked_flags[-1]) == 0 and self.enemy_attack_map[-1][unit.x][unit.y] > 0:
                    self.information_attacked_flags.append([unit.x, unit.y])

        if not self.action_phase:
            self.action_phase = True


        """
        if(len(self.enemy_movement_map) <= game_state.turn_number):
            # Create more slots for enemy movement map
            self.enemy_movement_map.append([])
            for x in range(0, self.ARENA_SIZE):
                self.enemy_movement_map.append([])
                for _ in range(0, self.ARENA_SIZE):
                    self.enemy_movement_map[x].append(0)
            
            # Create another array for spawn locations
            for unit in game_state.units:
                if(unit not in self.enemy_spawn_locs and unit.player_index == 1 and not unit.stationary):
                    self.enemy_spawn_locs.append([unit])

        if(len(self.enemy_movement_path) <= game_state.turn_number):
            # Create more slots for enemy movement path
            self.enemy_movement_path.append([])

        self.enemy_movement_path[game_state.turn_number].append([])
        for unit in game_state.units:
            if not [unit.x, unit.y] in self.enemy_movement_path[game_state.turn_number][len(self.enemy_movement_path[game_state.turn_number])-1]:
                self.enemy_movement_path[game_state.turn_number].append([unit.x, unit.y])
            for loc in game_state.game_map.get_locations_in_range([unit.x, unit.y], unit.range):
                self.enemy_movement_map[game_state.turn_number][loc[0]][loc[1]] += 1
        """
            
class Build:
    def __init__(self, unit_type, loc, probability):
        """self.config = config
        self.game_state_string = game_state_string
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]"""


        self.unit_type = unit_type
        self.loc = loc
        self.probability = probability

class BuildSet:
    def __init__(self, build_list, probability, cost):

        self.build_list = build_list
        self.probability = probability
        self.cost = cost

            

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
