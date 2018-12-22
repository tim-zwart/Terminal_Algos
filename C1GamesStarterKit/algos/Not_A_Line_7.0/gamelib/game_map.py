import gamelib
import math
import warnings
from .unit import GameUnit

class GameMap:
    """Holds data about the current game map and provides functions
    useful for getting information related to the map.

    Note that the game board is stored as a 2 dimensional array representing each tile on
    the board. Each tile is yet another array containing the units located at
    the x,y coordinates specified in the first two indices. So getting the 2nd
    of 3 units located at (12, 13) would look like: `unit = instance_of_game_map[12,13][1]`

    Attributes:
        * config (JSON): Contains information about the game
        * ARENA_SIZE (int): The size of the arena.
        * HALF_ARENA (int): Half of the size of the arena.
        * TOP_RIGHT (int): A constant that represents the top right edge
        * TOP_LEFT (int): A constant that represents the top left edge
        * BOTTOM_LEFT (int): Hidden challange! Can you guess what this constant represents???
        * BOTTOM_RIGHT (int): A constant that represents the bottom right edge

    """
    def __init__(self, config, storage):
        """Initializes constants and game map

        Args:
            * config (JSON): Contains information about the game

        """
        self.config = config
        self.ARENA_SIZE = 28
        self.HALF_ARENA = int(self.ARENA_SIZE / 2)
        self.TOP_RIGHT = 0
        self.TOP_LEFT = 1
        self.BOTTOM_LEFT = 2
        self.BOTTOM_RIGHT = 3
        self.map = self.__empty_grid()
        self.__start = [13,0]

        self.storage = storage

        self.edges = self.get_edges()

        self.in_arena_bounds = storage.in_arena_bounds

        self.locs_in_range_3 = storage.locs_in_range_3
        self.locs_in_range_5 = storage.locs_in_range_5

        self.locs_in_range_3_sorted = storage.split_locs_3
        self.locs_in_range_5_sorted = storage.split_locs_5

    
    def __getitem__(self, location):
        if len(location) == 2 and self.in_arena_bounds(location):
            x,y = location
            return self.map[x][y]
        self._invalid_coordinates(location)

    def __setitem__(self, location, val):
        if type(location) == tuple and len(location) == 2 and self.in_arena_bounds(location):
            self.map[location[0]][location[1]] = val
            return
        self._invalid_coordinates(location)

    def __iter__(self):
        self.__start = [13,0]
        return self
    
    def __next__(self):
        location = self.__start
        if location == [15,27]:
            raise StopIteration
        new_location = [location[0]+1, location[1]]
        while not self.in_arena_bounds(new_location) and not location == [14,27]:
            if new_location[0] == self.ARENA_SIZE:
                new_location = [0, new_location[1]+1]
            else:
                new_location = [new_location[0]+1, new_location[1]]
        self.__start = new_location
        return location 

    def __empty_grid(self):
        grid = []
        for x in range(0, self.ARENA_SIZE):
            grid.append([])
            for _ in range(0, self.ARENA_SIZE):
                grid[x].append([])
        return grid

    def _invalid_coordinates(self, location):
        warnings.warn("{} is out of bounds.".format(str(location)))


    def get_edge_locations(self, quadrant_description):
        """Takes in an edge description and returns a list of locations.
        
        Args:
            * quadrant_description: A constant corresponding to an edge. Valid quadrant descriptions are
                * GameMap.TOP_RIGHT
                * GameMap.TOP_LEFT
                * GameMap.BOTTOM_RIGHT
                * GameMap.BOTTOM_LEFT

        Returns:
            A list of locations corresponding to the requested edge

        """
        if not quadrant_description in [self.TOP_LEFT, self.TOP_RIGHT, self.BOTTOM_LEFT, self.BOTTOM_RIGHT]:
            warnings.warn("Passed invalid quadrent_description '{}'. See the documentation for valid inputs for get_edge_locations.".format(quadrant_description))

        return self.edges[quadrant_description]

    def get_edges(self):
        return self.storage.edges
    
    def add_unit(self, unit_type, location, player_index=0, id=None, path_target=None):
        """Add a single GameUnit to the map at the given location.

        Args:
            * unit_type: The type of the new unit
            * location: The location of the new unit
            * player_index: The index corresponding to the player controlling the new unit, 0 for you 1 for the enemy

        This function does not affect your turn and only changes the data stored in GameMap. The intended use of this function
        is to allow you to create arbitrary gamestates. Using this function on the GameMap inside game_state can cause your algo to crash.
        """
        if not self.in_arena_bounds(location):
            self._invalid_coordinates(location)
        if player_index < 0 or player_index > 1:
            warnings.warn("Player index {} is invalid. Player index should be 0 or 1.".format(player_index))

        x, y = location
        new_unit = GameUnit(unit_type, self.config, player_index, id, None, location[0], location[1])
        new_unit.path_target = path_target
        if not new_unit.stationary:
            self.map[x][y].append(new_unit)
        else:
            self.map[x][y] = [new_unit]

    def remove_unit(self, location):
        """Remove all units on the map in the given location.

        Args:
            * location: The location that you will empty of units

        This function does not affect your turn and only changes the data stored in GameMap. The intended use of this function
        is to allow you to create arbitrary gamestates. Using this function on the GameMap inside game_state can cause your algo to crash.
        """
        if not self.in_arena_bounds(location):
            self._invalid_coordinates(location)
        
        x, y = location
        self.map[x][y] = []

    def get_locations_in_range_sorted(self, location, radius):
        if radius == 3:
            return self.loc_in_range_3_sorted
        elif radius == 5:
            return self.loc_in_range_5_sorted
        else:
            return -1


    def get_locations_in_range(self, location, radius, bounds=True, raw=False):
        """Gets locations in a circular area around a location

        Args:
            * location: The center of our search area
            * radius: The radius of our search area

        Returns:
            The locations that are within our search area

        """
        if radius < 0 or radius > self.ARENA_SIZE:
            warnings.warn("Radius {} was passed to get_locations_in_range. Expected integer between 0 and {}".format(radius, self.ARENA_SIZE))
        if bounds and not self.in_arena_bounds(location):
            self._invalid_coordinates(location)

        x, y = location
        locations = []

        if not raw and (radius == 3 or radius == 5):
            if radius == 3:
                locs_in_range = self.locs_in_range_3
            else:
                locs_in_range = self.locs_in_range_5
            if not bounds and location == [0,0]:
                return locs_in_range
            for loc in locs_in_range:
                new_x = loc[0] + x
                new_y = loc[1] + y
                if not bounds or self.in_arena_bounds([new_x, new_y]):
                    locations.append([new_x, new_y])

            return locations


        for i in range(int(x - radius), int(x + radius + 1)):
            for j in range(int(y - radius), int(y + radius + 1)):
                new_location = [i, j]

                # A unit with a given range affects all locations who's centers are within that range + 0.51 so we add 0.51 here
                if ((not bounds) or self.in_arena_bounds(new_location)) and self.distance_between_locations(location, new_location) < radius + 0.51:
                    locations.append(new_location)

        return locations

    def distance_between_locations(self, location_1, location_2):
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

class Map:

    def __init__(config):
        self.config = config
        self.grid = self.__empty_grid()

    def __empty_grid(self):
        grid = []
        for x in range(0, self.ARENA_SIZE):
            grid.append([])
            for _ in range(0, self.ARENA_SIZE):
                grid[x].append([])
        return grid
    
    def __getitem__(self, location):
        if len(location) == 2 and self.in_arena_bounds(location):
            x,y = location
            return self.grid[x][y]
        self._invalid_coordinates(location)

    def __setitem__(self, location, val):
        if type(location) == tuple and len(location) == 2 and self.in_arena_bounds(location):
            self.grid[location[0]][location[1]] = val
            return
        self._invalid_coordinates(location)

    def _invalid_coordinates(self, location):
        warnings.warn("{} is out of bounds.".format(str(location)))


class MapLoc:

    def __init__(config):
        self.config = config

        self.defencePriority = 0
        self.offencePriority = 0
        self.priority = 0
