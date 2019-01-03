from .game_state import GameState, GameUnit
import sys
import warnings
import gamelib
import time

class AdvancedGameState(GameState):
    """A version of gamestate with access to a few more advanced functions

    """
    def get_target(self, attacking_unit, information_start=0, firewall_start=0):
        """Returns target of given unit based on current map of the game board. 
        A Unit can often have many other units in range, and Units that attack do so once each frame.

        Their targeting priority is as follows:
            Infantry > Nearest Unit > Lowest Stability > Lowest Y position > Closest to edge (Highest distance of X from the boards center, 13.5)

        Args:
            * attacking_unit: A GameUnit

        Returns:
            The GameUnit this unit would choose to attack.

        """
        
        from .game_state import SCRAMBLER, is_stationary
        
        if not isinstance(attacking_unit, GameUnit):
            warnings.warn("Passed a {} to get_target as attacking_unit. Expected a GameUnit.".format(type(attacking_unit)))
            return

        attacker_location = [attacking_unit.x, attacking_unit.y]
        if attacking_unit.range == 3:
            possible_locations = self.locs_in_range_3_sorted
        else:
            possible_locations = self.locs_in_range_5_sorted
            
        #possible_locations = self.game_map.get_locations_in_range(attacker_location, attacking_unit.range)

        target = None
        target_stationary = True
        target_distance = sys.maxsize
        target_stability = sys.maxsize
        target_y = self.ARENA_SIZE
        target_x_distance = 0

        #attacking_unit_index = attacking_unit.player_index

        forget_about_stationary = attacking_unit.unit_type == SCRAMBLER

        unit_loc = attacking_unit.loc
        in_arena_bounds = self.game_map.in_arena_bounds
        game_map = self.game_map
        distance_between_locations = self.game_map.distance_between_locations

        index = 0

        for set_dist in possible_locations:
            
            dist = distance_between_locations(set_dist[0], [0, 0])

            skip_info = dist < information_start
            skip_fire = forget_about_stationary or dist < firewall_start
                
            if skip_fire and skip_info:
                continue
            
            for location in set_dist:
                
                location = [unit_loc[0] + location[0], unit_loc[1] + location[1]]

                #if (not in_arena_bounds(location)) or (skip_info and location[1] >= 14 == bool(attacking_unit_index)):
                #    continue
                
                if not in_arena_bounds(location):
                    continue

                units = game_map[location]
                for unit in units:
                    """
                    NOTE: scrambler units cannot attack firewalls so skip them if unit is firewall
                    """
                    if unit.player_index == attacking_unit.player_index or (skip_fire and is_stationary(unit.unit_type)) or (skip_info and not is_stationary(unit.unit_type)) or unit.stability <= 0:
                        continue

                    new_target = False
                    unit_stationary = unit.stationary
                    unit_distance = distance_between_locations(location, [attacking_unit.x, attacking_unit.y])
                    unit_stability = unit.stability
                    unit_y = unit.y
                    unit_x_distance = abs(self.HALF_ARENA - 0.5 - unit.x)

                    if target_stationary and not unit_stationary:
                        new_target = True
                    elif not target_stationary and unit_stationary:
                        continue
                    else:
                        if target_stability > unit_stability:
                            new_target = True
                        elif target_stability < unit_stability and not new_target:
                            continue
                        else:
                            if target_y > unit_y:
                                new_target = True
                            elif target_y < unit_y and not new_target:
                                continue       
                            else:
                                if target_x_distance < unit_x_distance:
                                    new_target = True
                    
                    if new_target:
                        target = unit
                        target_stationary = unit_stationary
                        target_distance = unit_distance
                        target_stability = unit_stability
                        target_y = unit_y
                        target_x_distance = unit_x_distance

                        if (not forget_about_stationary) and (not target_stationary):
                            forget_about_stationary = True

            if not target_stationary:
                break

        return target

    def get_target_2(self, attacking_unit, information_start=0, firewall_start=0):
        """Returns target of given unit based on current map of the game board. 
        A Unit can often have many other units in range, and Units that attack do so once each frame.

        Their targeting priority is as follows:
            Infantry > Nearest Unit > Lowest Stability > Lowest Y position > Closest to edge (Highest distance of X from the boards center, 13.5)

        Args:
            * attacking_unit: A GameUnit

        Returns:
            The GameUnit this unit would choose to attack.

        """
        
        from .game_state import SCRAMBLER, is_stationary
        
        if not isinstance(attacking_unit, GameUnit):
            warnings.warn("Passed a {} to get_target as attacking_unit. Expected a GameUnit.".format(type(attacking_unit)))
            return

        attacker_location = [attacking_unit.x, attacking_unit.y]
        if attacking_unit.range == 3:
            possible_locations = self.locs_in_range_3_sorted
        else:
            possible_locations = self.locs_in_range_5_sorted
            
        #possible_locations = self.game_map.get_locations_in_range(attacker_location, attacking_unit.range)

        target = None
        target_stationary = True
        target_distance = sys.maxsize
        target_stability = sys.maxsize
        target_y = self.ARENA_SIZE
        target_x_distance = 0

        attacking_unit_index = attacking_unit.player_index

        forget_about_stationary = attacking_unit.unit_type == SCRAMBLER

        unit_loc = attacking_unit.loc
        in_arena_bounds = self.game_map.in_arena_bounds
        game_map = self.game_map
        distance_between_locations = self.game_map.distance_between_locations

        index = 0

        for set_dist in possible_locations:
            
            dist = distance_between_locations(set_dist[0], [0, 0])

            skip_info = dist < information_start
            skip_fire = forget_about_stationary or dist < firewall_start
                
            if skip_fire and skip_info:
                continue
            
            for location in set_dist:
                
                location = [unit_loc[0] + location[0], unit_loc[1] + location[1]]

                if (not in_arena_bounds(location)) or (skip_info and location[1] >= 14 == bool(attacking_unit_index)):
                    continue
                
                #if not in_arena_bounds(location):
                #    continue

                units = game_map[location]
                for unit in units:
                    """
                    NOTE: scrambler units cannot attack firewalls so skip them if unit is firewall
                    """
                    if unit.player_index == attacking_unit_index or (skip_fire and is_stationary(unit.unit_type)) or (skip_info and not is_stationary(unit.unit_type)) or unit.stability <= 0:
                        continue

                    new_target = False
                    unit_stationary = unit.stationary
                    unit_distance = distance_between_locations(location, [attacking_unit.x, attacking_unit.y])
                    unit_stability = unit.stability
                    unit_y = unit.y
                    unit_x_distance = abs(self.HALF_ARENA - 0.5 - unit.x)

                    if target_stationary and not unit_stationary:
                        new_target = True
                    elif not target_stationary and unit_stationary:
                        continue
                    else:
                        if target_stability > unit_stability:
                            new_target = True
                        elif target_stability < unit_stability and not new_target:
                            continue
                        else:
                            if target_y > unit_y:
                                new_target = True
                            elif target_y < unit_y and not new_target:
                                continue       
                            else:
                                if target_x_distance < unit_x_distance:
                                    new_target = True
                    
                    if new_target:
                        target = unit
                        target_stationary = unit_stationary
                        target_distance = unit_distance
                        target_stability = unit_stability
                        target_y = unit_y
                        target_x_distance = unit_x_distance

                        if (not forget_about_stationary) and (not target_stationary):
                            forget_about_stationary = True

            if not target_stationary:
                break

        return target


    def get_attackers(self, location, player_index):
        """Gets the destructors threatening a given location

        Args:
            * location: The location of a hypothetical defender
            * player_index: The index corresponding to the defending player, 0 for you 1 for the enemy

        Returns:
            A list of destructors that would attack a unit controlled by the given player at the given location

        """
        
        from .game_state import DESTRUCTOR, UNIT_TYPE_TO_INDEX

        if not player_index == 0 and not player_index == 1:
            self._invalid_player_index(player_index)
        if not self.game_map.in_arena_bounds(location):
            warnings.warn("Location {} is not in the arena bounds.".format(location))

        attackers = []
        """
        Get locations in the range of DESTRUCTOR units
        """
        possible_locations= self.game_map.get_locations_in_range(location, self.config["unitInformation"][UNIT_TYPE_TO_INDEX[DESTRUCTOR]]["range"])
        for location in possible_locations:
            for unit in self.game_map[location]:
                if unit.unit_type == DESTRUCTOR and unit.player_index != player_index:
                    attackers.append(unit)
        return attackers
