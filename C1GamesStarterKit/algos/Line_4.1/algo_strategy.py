import gamelib
import random
import math
import warnings
import json
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
        self.round = 0
        self.lastAttack = 0
        self.EMP = 0
        self.PING = 1

        self.opponent_movement_path = []
        self.opponent_pressure_heatmap = []

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


    def on_turn(self, turn_state):
        self.round += 1
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state,False)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        #gamelib.debug_write("\n\n\nData from this turn:" + turn_state + "\n\n\n")
        game_state.suppress_warnings(True)  #Uncomment this line to suppress warnings.
        self.starter_strategy(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safey be replaced for your custom algo.
    """
    def starter_strategy(self, game_state):
        """
        Build the C1 logo. Calling this method first prioritises
        resources to build and repair the logo before spending them 
        on anything else.
        """
        self.build_base_defences(game_state)

        """
        Then build additional defenses.
        """
        self.build_encryptors(game_state)

        """
        Finally deploy our information units to attack.
        """
        self.deploy_attackers(game_state)

    # Here we make the base defences!
    def build_base_defences(self, game_state):
        destructor_locations = [[ 1, 12],[ 25, 12],[ 26, 12],[ 2, 11],[ 7, 11],[ 10, 11],[ 13, 11],[ 16, 11],[ 19, 11],[ 22, 11],[ 24, 11],[ 25, 11],[ 3, 10],[ 4, 10],[ 4, 9],[ 5, 9],[ 6, 9],[ 5, 8],[ 6, 8],[ 6, 7]]
        filter_locations = [[ 0, 13],[ 1, 13],[ 25, 13],[ 26, 13],[ 27, 13],[ 2, 12],[ 7, 12],[ 10, 12],[ 13, 12],[ 16, 12],[ 19, 12],[ 22, 12],[ 24, 12],[ 3, 11],[ 6, 11],[ 8, 11],[ 9, 11],[ 11, 11],[ 12, 11],[ 14, 11],[ 15, 11],[ 17, 11],[ 18, 11],[ 20, 11],[ 21, 11],[ 23, 11]]
        encryptor_locations = [[ 7, 9],[ 8, 9],[ 9, 9],[ 10, 9],[ 11, 9],[ 12, 9],[ 13, 9],[ 14, 9],[ 15, 9],[ 16, 9],[ 17, 9],[ 18, 9],[ 7, 8],[ 8, 8],[ 9, 8],[ 10, 8],[ 11, 8],[ 12, 8],[ 13, 8],[ 14, 8],[ 15, 8],[ 16, 8],[ 17, 8],[ 18, 8],[ 7, 7],[ 8, 7],[ 9, 7],[ 10, 7],[ 11, 7],[ 12, 7],[ 13, 7],[ 14, 7],[ 15, 7],[ 16, 7],[ 17, 7],[ 18, 7]]
        
        for loc in destructor_locations:
            if game_state.get_resource(game_state.CORES) < 1:
                return
            if loc[1] >= 11:
                protected = {
                    "forward": False,
                    "left": False,
                    "right": False
                }

                if game_state.contains_stationary_unit([loc[0], loc[1]+1]): # Forward
                    protected["forward"] = True
                if not game_state.game_map.in_arena_bounds([loc[0]-1, loc[1]]) or game_state.contains_stationary_unit([loc[0]-1, loc[1]]): # Left
                    protected["left"] = True
                if not game_state.game_map.in_arena_bounds([loc[0]+1, loc[1]]) or game_state.contains_stationary_unit([loc[0]+1, loc[1]]): # Right
                    protected["right"] = True

                if game_state.get_resource(game_state.CORES) < (not game_state.contains_stationary_unit(loc))*3 + (not protected["forward"]) + (not protected["left"]) + (not protected["right"]):
                    return

                for f_loc in filter_locations:
                    if protected["forward"] and protected["left"] and protected["right"]:
                        break
                    elif f_loc == [loc[0], loc[1]+1]: # Forward
                        protected["forward"] = True
                        game_state.attempt_spawn(FILTER, f_loc)
                    elif f_loc == [loc[0]-1, loc[1]]: # Left
                        protected["left"] = True
                        game_state.attempt_spawn(FILTER, f_loc)
                    elif f_loc == [loc[0]+1, loc[1]]: # Right
                        protected["right"] = True
                        game_state.attempt_spawn(FILTER, f_loc)

                game_state.attempt_spawn(DESTRUCTOR, loc)

        for f_loc in reversed(filter_locations):
            game_state.attempt_spawn(FILTER, f_loc)
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)
        game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)
        
        """



        # Necessary to attack
        pathing_filter_locations = [[19,8], [21,9]]
        game_state.attempt_spawn(FILTER, pathing_filter_locations)

        # The most important, because they can cover the entire map (except for one tiny gap, not expected to be an issue)
        destructor_locations = [[2,11],[10,10],[17,10],[25,11]]
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)

        # Protect the side corners
        side_protection_filter_locations = [[ 0, 13],[ 1, 13],[ 26, 13],[ 27, 13],[ 2, 13],[ 25, 13],[ 3,12],[ 4, 11],[ 5, 11],[ 23, 12],[ 24, 13]]
        game_state.attempt_spawn(FILTER, side_protection_filter_locations)

        important_side_protection_destructor_locations = [[ 1, 12],[ 26, 12],[ 3, 10],[ 24, 10]]
        game_state.attempt_spawn(DESTRUCTOR, important_side_protection_destructor_locations)

        # Finish the line of filters
        for x in reversed(range(8, 23)):
            game_state.attempt_spawn(FILTER, [x, 11])

        # A couple more protected destructors to evenly spread out defence
        secondary_defensive_pair_locations = [[[7,10],[7,11]], [[21,10],[21,11]], [[14,10],[14,11]]]
        for set in reversed(secondary_defensive_pair_locations):
            if  len(set) == 1:
                game_state.attempt_spawn(DESTRUCTOR, set)
            elif len(set) == 2:
                game_state.attempt_spawn(DESTRUCTOR, set[0])
                game_state.attempt_spawn(FILTER, set[1])

        # Finish the line of destructors
        for x in reversed(range(8, 24)):
            game_state.attempt_spawn(DESTRUCTOR, [x, 10])

        # Build a few more destructors at the sides for "starfish" (AI bot) style strategies
        additional_side_protection_destructor_locations = [[ 1, 12],[ 2, 12],[ 25, 12],[ 26, 12],[ 3, 11],[ 24, 11],[ 3, 10],[ 4, 10],[ 5, 8],[ 5, 9],[ 5, 10],[ 4, 9],[ 24, 12],[ 23, 11],[ 24, 10]]
        game_state.attempt_spawn(DESTRUCTOR, additional_side_protection_destructor_locations)
        """
        # Build encryptors

    def build_encryptors(self, game_state):
        """
        Then lets boost our offense by building some encryptors to shield 
        our information units. Lets put them near the front because the 
        shields decay over time, so shields closer to the action 
        are more effective.
        """
        #encryptor_locations = [[ 6, 8],[ 7, 8],[ 8, 8],[ 9, 8],[ 10, 8],[ 11, 8],[ 12, 8],[ 13, 8],[ 14, 8],[ 15, 8],[ 16, 8],[ 17, 8],[ 6, 7],[ 7, 7],[ 8, 7],[ 9, 7],[ 10, 7],[ 11, 7],[ 12, 7],[ 13, 7],[ 14, 7],[ 15, 7],[ 16, 7],[ 17, 7],[ 7, 6],[ 8, 6],[ 9, 6],[ 10, 6],[ 11, 6],[ 12, 6],[ 13, 6],[ 14, 6],[ 15, 6],[ 16, 6],[ 17, 6]]
        #game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)

    def deploy_attackers(self, game_state):
        if(game_state.number_affordable(EMP) >= 2): # Only diff between 2.1 and 2.11
            game_state.attempt_spawn(EMP, [24, 10], game_state.number_affordable(EMP))


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
        a=1#game_state = gamelib.GameState(self.config, turn_state,True)

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
