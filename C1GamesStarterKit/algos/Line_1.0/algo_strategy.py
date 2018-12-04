import gamelib
import random
import math
import warnings
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

    def on_game_start(self, config):
        self.round = 0
        self.lastAttack = 0
        self.EMP = 0
        self.PING = 1
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
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
        """
        Build the C1 logo. Calling this method first prioritises
        resources to build and repair the logo before spending them 
        on anything else.
        """
        self.build_base_defences(game_state)

        """
        Then build additional defenses.
        """
        self.build_defences(game_state)

        """
        Finally deploy our information units to attack.
        """
        self.deploy_attackers(game_state)

    # Here we make the base defences!
    def build_base_defences(self, game_state):
        # Necessary to attack
        pathing_filter_locations = [[13,1], [14,2]]
        game_state.attempt_spawn(FILTER, pathing_filter_locations)

        # The most important, because they can cover the entire map (except for one tiny gap, not expected to be an issue)
        destructor_locations = [[2,11],[10,12],[17,12],[24,12]]
        game_state.attempt_spawn(DESTRUCTOR, destructor_locations)

        # Protect the important destructors and the side corners
        crucial_filter_locations = [[0,13],[1,13],[2,13],[9,13],[10,13],[11,13],[16,13],[17,13],[18,13],[23,13],[24,13],[25,13],[26,13],[27,13]]
        game_state.attempt_spawn(FILTER, crucial_filter_locations)

        # A couple more protected destructors to evenly spread out defence
        secondary_defensive_pair_locations = [[[3,12],[3,13]], [[6,12],[6,13]], [[14,12],[14,13]], [[21,12],[21,13]], [[26,12],[26,13]]]
        for set in reversed(secondary_defensive_pair_locations):
            if  len(set) == 1:
                game_state.attempt_spawn(DESTRUCTOR, set)
            elif len(set) == 2:
                game_state.attempt_spawn(DESTRUCTOR, set[0])
                game_state.attempt_spawn(FILTER, set[1])

        # Finish the line of filters
        for x in reversed(range(7, 26)):
            game_state.attempt_spawn(FILTER, [x, 13])

        # Finish the line of destructors
        for x in reversed(range(7, 27)):
            game_state.attempt_spawn(DESTRUCTOR, [x, 12])

        # Build a few more destructors at the opening
        gap_protection_destructors = [[1,12],[2,12],[3,10],[3,11]]
        game_state.attempt_spawn(DESTRUCTOR, gap_protection_destructors)

        # Build encryptors

    def build_defences(self, game_state):
        """
        Then lets boost our offense by building some encryptors to shield 
        our information units. Lets put them near the front because the 
        shields decay over time, so shields closer to the action 
        are more effective.
        """
        encryptor_locations = [[3,10], [4,10], [5,10], [6,10], [7,10], [8,10], [3,9], [4,9], [5,9], [6,9], [7,9], [8,9], [4,8], [5,8], [6,8], [7,8], [8,8]]
        for location in encryptor_locations:
            if game_state.can_spawn(ENCRYPTOR, location):
                game_state.attempt_spawn(ENCRYPTOR, location)

    def deploy_attackers(self, game_state):
        """
        First lets check if we have 10 bits, if we don't we lets wait for 
        a turn where we do.
        """

        if (game_state.get_resource(game_state.BITS) < 10 + int(self.round/5) or (not game_state.contains_stationary_unit([13, 1])) or (not game_state.contains_stationary_unit([14, 2]))):
            return

        if(self.lastAttack == self.EMP):
            game_state.attempt_spawn(PING, [14, 0], int(game_state.get_resource(game_state.BITS)))
            self.lastAttack = self.PING
            return
        
        self.lastAttack = self.EMP
        
        """
        First lets deploy an EMP long range unit to destroy firewalls for us.
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
        

        if game_state.can_spawn(EMP, [14, 0], nEMP):
            game_state.attempt_spawn(EMP, [14, 0], nEMP)

        """
        Now lets send out 3 Pings to hopefully score, we can spawn multiple 
        information units in the same location.
        """
        """
        if game_state.can_spawn(PING, [14, 0], 5):
            game_state.attempt_spawn(PING, [14,0], 5)
        """
        """
        NOTE: the locations we used above to spawn information units may become 
        blocked by our own firewalls. We'll leave it to you to fix that issue 
        yourselves.

        Lastly lets send out Scramblers to help destroy enemy information units.
        A complex algo would predict where the enemy is going to send units and 
        develop its strategy around that. But this algo is simple so lets just 
        send out scramblers in random locations and hope for the best.   
        """

        """
        While we have remaining bits to spend lets send out scramblers.
        """
        while game_state.get_resource(game_state.BITS) >= game_state.type_cost(SCRAMBLER):
            game_state.attempt_spawn(SCRAMBLER, [15,1])
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
