import cProfile
import timeit
import gamelib
import random
import math
import warnings
import json
import operator
import time
import copy
from sys import maxsize

"""x
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

        # Define possible attacking methods
        global PING_RUSH, SCRAMBLER_DEFENCE, EMP_ATTACK, HYBRID
        PING_RUSH = 0
        SCRAMBLER_DEFENCE = 1
        EMP_ATTACK = 2
        HYBRID = 3

        ALL_UNITS = [PING, EMP, SCRAMBLER, FILTER, ENCRYPTOR, DESTRUCTOR]
        FIREWALL_TYPES = [FILTER, ENCRYPTOR, DESTRUCTOR]
        self.ARENA_SIZE = 28
        self.HALF_ARENA = int(self.ARENA_SIZE / 2)

        self.storage = gamelib.Storage(config)
        
        self.lastAttack = 0
        self.EMP = 0
        self.PING = 1
        self.ideal_map = gamelib.GameMap(config, self.storage)
        self.simulation = None
        self.simulation2 = None

        self.action_phase = False
        self.units_sent = False
        self.emp_spawn_loc = [24, 10]

        self.self_movement_map = []
        self.self_movement_path = []
        self.information_attacked_flags = []

        self.enemy_spawn_locs = []
        self.enemy_movement_map = []
        self.enemy_movement_path = []
        self.enemy_attack_map = []
        self.enemy_attack_intensity = []

        self.destructor_locations = [[ 1, 12],[ 25, 12],[ 26, 12],[ 2, 11],[ 7, 11],[ 10, 11],[ 13, 11],[ 16, 11],[ 19, 11],[ 22, 11],[ 24, 11],[ 25, 11],[ 3, 10],[ 4, 10],[ 4, 9],[ 5, 9],[ 6, 9],[ 5, 8],[ 6, 8],[ 6, 7]]
        self.filter_locations = [[ 0, 13],[ 1, 13],[ 25, 13],[ 26, 13],[ 27, 13],[ 2, 12],[ 7, 12],[ 10, 12],[ 13, 12],[ 16, 12],[ 19, 12],[ 22, 12],[ 24, 12],[ 3, 11],[ 6, 11],[ 8, 11],[ 9, 11],[ 11, 11],[ 12, 11],[ 14, 11],[ 15, 11],[ 17, 11],[ 18, 11],[ 20, 11],[ 21, 11],[ 23, 11]]
        self.encryptor_locations = [[ 7, 9],[ 8, 9],[ 9, 9],[ 10, 9],[ 11, 9],[ 12, 9],[ 13, 9],[ 14, 9],[ 15, 9],[ 16, 9],[ 17, 9],[ 18, 9],[ 19, 9],[ 20, 9],[ 21, 9],[ 7, 8],[ 8, 8],[ 9, 8],[ 10, 8],[ 11, 8],[ 12, 8],[ 13, 8],[ 14, 8],[ 15, 8],[ 16, 8],[ 17, 8],[ 18, 8],[ 19, 8],[ 20, 8],[ 7, 7],[ 8, 7],[ 9, 7],[ 10, 7],[ 11, 7],[ 12, 7],[ 13, 7],[ 14, 7],[ 15, 7],[ 16, 7],[ 17, 7],[ 18, 7],[ 19, 7]]

        self.build_sets = []
        self.n_simuls = []
        self.n_simuls_2 = []

        for loc in self.destructor_locations:
            self.ideal_map.add_unit(DESTRUCTOR, loc, 0)
            build_list = [Build(DESTRUCTOR, loc, 0)]

            for filter in self.filter_locations:
                if self.ideal_map.distance_between_locations(loc, filter) == 1 or (loc == [26, 12] and filter == [27, 13]) or (loc == [1, 12] and filter == [0, 13]):
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

        self.turn_state = turn_state

        if self.action_phase:
            self.action_phase = False

        game_state = gamelib.GameState(self.config, turn_state, self.storage)

        #if self.simulation2 != None and game_state.turn_number % 2 != 0:
        #    self.simulation2.game_state.game_map.calculate()
        #    self.simulation2.game_state.game_map.show_board(game_state.game_map.TOP_LEFT)
        #    if self.simulation2.game_state.game_map == game_state.game_map:
        #        gamelib.debug_write("YAAAYYYYYYYYY")
        #    gamelib.debug_write("yay equal")


        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  #Uncomment this line to suppress warnings.
        self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def starter_strategy(self, game_state):
        import timeit

        self.turn_start = time.clock()

        self.build_base_defences(game_state)
        
        self.deploy_attackers(game_state)

    # Here we make the base defences!
    def build_base_defences(self, game_state):
        # Calculate probability of building
        necessary_sets = []
        unit_path = game_state.find_path_to_edges(self.emp_spawn_loc)

        for build_set in self.build_sets:
            build_set.probability = 0
            necessary = False
            build_set.cost = 0
            n_missing = 0
            any_built = False

            for build in build_set.build_list:
                build.probability = 0
                if not game_state.contains_stationary_unit(build.loc):
                    if build.unit_type == FILTER:
                        enemy_attack_filter_loc = 0
                        enemy_attack_destructor_loc = 0
                        if len(self.enemy_attack_map) > 0:
                            for i in range(1, min(3, len(self.enemy_attack_map))):
                                enemy_attack_filter_loc += self.enemy_attack_map[-i][build.loc[0]][build.loc[1]]
                                enemy_attack_destructor_loc += self.enemy_attack_map[-i][build_set.build_list[0].loc[0]][build_set.build_list[0].loc[1]]
                        
                        if len(build_set.build_list) == 4:

                            if enemy_attack_filter_loc > 0 and enemy_attack_destructor_loc == 0 and build.loc[1] == build_set.build_list[0].loc[1]+1:
                                build.probability = -1
                                gamelib.debug_write("Not flagging filter for rebuilding at location ({}, {}) because it would just be destroyed".format(build.loc[0], build.loc[1]))
                            else:
                                build_set.cost += 1
                                n_missing += 1
                        else:
                            build_set.cost += 1
                            n_missing += 1

                        if game_state.contains_stationary_unit(build_set.build_list[0].loc):
                            build_set.probability += enemy_attack_destructor_loc

                        
                                
                    elif build.unit_type == DESTRUCTOR:
                        # Check to what extent we attack where they are moving
                        n_attack_locs = 0
                        n_missing += 1
                        
                        for loc in self.ideal_map.get_locations_in_range(build.loc, 3.0):
                            for i in range(1, min(3, len(self.enemy_movement_map))):
                                if self.enemy_movement_map[-i][loc[0]][loc[1]] > 0:
                                    n_attack_locs += 1
                                    continue
                                    
                        build_set.probability += n_attack_locs * 0.5

                        build_set.cost += 3
                        
                    elif build.unit_type == ENCRYPTOR:
                        n_missing += 1
                        closeness_score = 0
                        closeness_score_2 = 0
                        emp_iter_2 = -1
                        emp_iter_3 = -1
                        curr_index = len(unit_path)

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
                            emp_iter = -1
                            attacked_loc = False

                            try:
                                emp_iter = unit_path.index(loc)
                            except:
                                pass

                            if emp_iter >= 0 and len(self.enemy_attack_map) > 0:
                                for i in range(1, min(3, len(self.enemy_attack_map))):
                                    if self.enemy_attack_map[-i][loc[0]][loc[1]] > 0:
                                        attacked_loc = True
                                        break

                                if attacked_loc and emp_iter < curr_index:
                                    closeness_score = 4 - self.ideal_map.distance_between_locations(unit_path[emp_iter], build.loc)

                        if closeness_score > 0:
                            build_set.probability += closeness_score * 0.3 + (len(unit_path)*2 - emp_iter) / (len(unit_path)*20)
                            
                        if closeness_score_2 > 0:
                            build_set.probability += closeness_score_2 * 0.3 * ((10.0 / 1.5) - (emp_iter_3 - emp_iter_2)) / (10.0 / 1.5)

                        build_set.cost += 4
                    
                    unit_path_iter = -1
                    try:
                        unit_path_iter = unit_path.index(build.loc)
                    except:
                        pass

                    if unit_path_iter >= 0:
                        build_set.probability += (len(unit_path)*2 - unit_path_iter) / (len(unit_path)*2) / 8

                else:
                    build.probability = -1
                    if game_state.game_map[build.loc][0].stability < game_state.game_map[build.loc][0].max_stability/2:
                        game_state.attempt_remove(build.loc)
                    if not any_built:
                        any_built = True

            if n_missing > 0:
                necessary_sets.append(build_set)
                if any_built:
                    build_set.probability += 2

        necessary_sets.sort(key=operator.attrgetter('probability'), reverse=True)
        #random.shuffle(necessary_sets)

        build_combos = []
        
        a=0

        for build_set in necessary_sets:
            if a < 5:
                pass
            if game_state.get_resource(game_state.CORES) < build_set.cost:
                return
            gamelib.debug_write("Building a set with probability {} at location".format(build_set.probability))
            for build in build_set.build_list:
                if build.probability >= 0:
                    gamelib.debug_write("({}, {})".format(build.loc[0], build.loc[1]))
                    game_state.attempt_spawn(build.unit_type, build.loc)
            a+=1
        

    def deploy_attackers(self, game_state):

        # Determine unit attack type
        import cProfile, pstats, io
        pr = cProfile.Profile()
        pr.enable()
        
        #start_time = time.clock()

        base_simul = gamelib.Simulator(self.config, self.turn_state, self.storage)
        base_simul.calculate()
        last_ideal = 0
        """
        time_start = time.clock()
        for _ in range(0, 100):
            simul = gamelib.Simulator(self.config, self.turn_state, self.storage)

            simul.game_state.game_map.copy_pathing(base_simul.game_state.game_map.pathfinding_map)
            simul.calculated = True

            simul.game_state.attempt_add(EMP, self.emp_spawn_loc, game_state.number_affordable(EMP), 0)
            enemy_info_spawn = [27-24, 27-10]
            simul.game_state.attempt_add(EMP, enemy_info_spawn, game_state.number_affordable(EMP, 1), 1)
            simul.simulate()
            last_ideal = simul.idealness()

        time_mid = time.clock()
        for _ in range(0, 100):
            simul = gamelib.Simulator_2(self.config, self.turn_state, self.storage)

            simul.game_state.game_map.copy_pathing(base_simul.game_state.game_map.pathfinding_map)
            simul.calculated = True

            simul.game_state.attempt_add(EMP, self.emp_spawn_loc, game_state.number_affordable(EMP), 0)
            enemy_info_spawn = [27-24, 27-10]
            simul.game_state.attempt_add(EMP, enemy_info_spawn, game_state.number_affordable(EMP, 1), 1)
            simul.simulate()
            last_ideal = simul.idealness()
        time_end = time.clock()

        """

        attacks = []

        # Check all possible attacks from the enemy
        for x in range(0, 28):
            if x < 14:
                y = x + 14
            else:
                y = 41 - x

            if game_state.can_spawn(SCRAMBLER, [x, y], 1, 1):

                # Check EMPs
                simul = gamelib.Simulator(self.config, self.turn_state, self.storage)

                simul.game_state.game_map.copy_pathing(base_simul.game_state.game_map.pathfinding_map)
                simul.calculated = True

                enemy_info_spawn = [x, y]
                simul.game_state.attempt_add(EMP, enemy_info_spawn, game_state.number_affordable(EMP, 1), 1)
                simul.simulate()
                attacks.append(gamelib.Possible_Attack(EMP, enemy_info_spawn, simul.idealness()))

                # Check Scramblers                
                simul = gamelib.Simulator(self.config, self.turn_state, self.storage)

                simul.game_state.game_map.copy_pathing(base_simul.game_state.game_map.pathfinding_map)
                simul.calculated = True

                enemy_info_spawn = [x, y]
                simul.game_state.attempt_add(SCRAMBLER, enemy_info_spawn, game_state.number_affordable(SCRAMBLER, 1), 1)
                simul.simulate()
                attacks.append(gamelib.Possible_Attack(SCRAMBLER, enemy_info_spawn, simul.idealness()))

                # Check Pings                
                simul = gamelib.Simulator(self.config, self.turn_state, self.storage)

                simul.game_state.game_map.copy_pathing(base_simul.game_state.game_map.pathfinding_map)
                simul.calculated = True

                enemy_info_spawn = [x, y]
                simul.game_state.attempt_add(PING, enemy_info_spawn, game_state.number_affordable(PING, 1), 1)
                simul.simulate()
                attacks.append(gamelib.Possible_Attack(PING, enemy_info_spawn, simul.idealness()))


        attacks.sort(key=operator.attrgetter('idealness'), reverse=True)

        for i in range(0, 5):
            a = attacks[i]
            unit_type = ""
            if a.unit_type == "SI":
                unit_type = "SCRAMBLER"
            if a.unit_type == "EI":
                unit_type = "EMP"
            if a.unit_type == "PI":
                unit_type = "PING"
            gamelib.debug_write("Placing {} at {} causes idealness {}".format(unit_type, a.location, a.idealness))
        

        """
        for n_simul in range(0, 10000):

            if time.clock() - self.turn_start >= 5:
                gamelib.debug_write("Completed {} simulations this turn".format(n_simul))
                gamelib.debug_write("Last idealness: {}".format(last_ideal))
                self.n_simuls.append(n_simul)
                break

            #simul = gamelib.Simulator(self.config, self.turn_state, self.storage)
            #gamelib.debug_write("Initialization of simulator in {}s".format(time.clock()-start_time))

            #simul = copy.deepcopy(base_simul)

            simul = gamelib.Simulator(self.config, self.turn_state, self.storage)

            simul.game_state.game_map.copy_pathing(base_simul.game_state.game_map.pathfinding_map)
            simul.calculated = True

            simul.game_state.attempt_add(EMP, self.emp_spawn_loc, game_state.number_affordable(EMP), 0)
            enemy_info_spawn = [27-24, 27-10]
            simul.game_state.attempt_add(EMP, enemy_info_spawn, game_state.number_affordable(EMP, 1), 1)
            simul.simulate()
            last_ideal = simul.idealness()
        """
        #sim()
        #prun sim()
        #timeit.timeit(sim)

        #end_time = time.clock()
        #gamelib.debug_write("Finished simulation in {}s".format(end_time-start_time))
        
        # ... do something ...
        pr.disable()
        s = io.StringIO()
        sortby = 'cumulative'
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_stats()
        gamelib.debug_write(s.getvalue())
        
        """

        self.n_simuls.append(time_mid-time_start)
        self.n_simuls_2.append(time_end-time_mid)

        i=0
        for n in self.n_simuls:
            gamelib.debug_write("Time for turn {} is {}".format(i, n))
            i+=1
        i=0
        for n in self.n_simuls_2:
            gamelib.debug_write("Time for turn {} is {}".format(i, n))
            i+=1
        """

        #gamelib.debug_write("Maps equal is {}".format())


        # Do we need to defend?

        # Can we remove lots of lives?
        # Ping vs Scrambler

        # Do we do chip?
        # EMP vs Scrambler
        attack_type = EMP_ATTACK

        if attack_type == PING_RUSH:
            # Determine ideal number of pings
            pass
            
        elif attack_type == SCRAMBLER_DEFENCE:
            # Find ideal location to send them from
            pass

        elif attack_type == EMP_ATTACK:
            #if(game_state.number_affordable(EMP) >= 2):
            game_state.attempt_spawn(EMP, self.emp_spawn_loc, game_state.number_affordable(EMP))
            self.units_sent = True
            #else:
            #    self.units_sent = False

        elif attack_type == HYBRID:
            if game_state.get_resource(game_state.BITS) >= 7:
                nEMP = int((game_state.BITS-1) / 3)
                game_state.attempt_spawn(EMP, self.emp_spawn_loc, nEMP)
                game_state.attempt_spawn(SCRAMBLER, self.emp_spawn_loc, game_state.number_affordable(SCRAMBLER))
                self.units_sent = True
            else:
                self.units_sent = False


    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


    def parse_action_phase(self, turn_state):
        game_state = gamelib.GameState(self.config, turn_state, self.storage)

        self.simulation2 = self.simulation
        self.simulation = gamelib.Simulator(self.config, turn_state, self.storage)

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

            self.enemy_attack_intensity.append([])
            for x in range(0, self.ARENA_SIZE):
                self.enemy_attack_intensity[-1].append([])
                for _ in range(0, self.ARENA_SIZE):
                    self.enemy_attack_intensity[-1][x].append(0)

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
                    self.enemy_attack_intensity[-1][loc[0]][loc[1]] += unit.damage

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