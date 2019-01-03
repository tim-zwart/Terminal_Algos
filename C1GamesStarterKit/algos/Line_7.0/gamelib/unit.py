import gamelib

def is_stationary(unit_type, firewall_types):
    return unit_type in firewall_types

class GameUnit:
    """Holds information about a Unit. 

    Attributes:
        * unit_type (string): This unit's type
        * config (JSON): Contains information about the game
        * player_index (integer): The player that controls this unit. 0 for you, 1 for your opponent.
        * stability (integer): The health of the unit
        * x (integer): The x coordinate of the unit
        * y (integer): The y coordinate of the unit
        * stationary (bool): Whether or not this unit is a firewall
        * speed (float): A unit will move once every 1/speed frames
        * damage (int): The amount of damage this firwall unit will deal to enemy information.
        * damage_f (int): The amount of damage this information unit will deal to enemy firewalls.
        * damage_i (int): The amount of damage this information unit will deal to enemy information.
        * range (float): The effective range of this unit
        * stability (float): The current health of this unit
        * cost (int): The resource cost of this unit

    """
    def __init__(self, unit_type, config, player_index=None, id=None, stability=None, x=-1, y=-1, path_target=None):
        """ Initialize unit variables using args passed

        """
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

        self.unit_type = unit_type
        self.config = config
        self.player_index = player_index
        self.pending_removal = False
        self.x = x
        self.y = y
        self.loc = [x, y]
        self.__serialize_type()
        self.stability = self.max_stability if not stability else stability
        self.actual_stability = self.stability
        self.encryption = []
        self.id = id
        self.tiles_moved = 0

        self.d_target = None

        if id != None:
            self.target = GameUnit(SCRAMBLER, config, not player_index, None, None, x, y)
            self.d_target = 0

        # Dir:
        # 0: tr
        # 1: tl
        # 2: bl
        # 3: br
        self.path_target = path_target
        self.next_dir_up = True

        self.moved = False

    def __serialize_type(self):

        self.stationary = is_stationary(self.unit_type, FIREWALL_TYPES)
        type_config = self.config["unitInformation"][UNIT_TYPE_TO_INDEX[self.unit_type]]
        if self.stationary:
            self.speed = 0
            if self.unit_type == ENCRYPTOR:
                self.damage = type_config["shieldAmount"]
                self.encrypted_IDs = []
            else:
                self.damage = type_config["damage"]
        else:
            self.speed = type_config["speed"]
            self.damage_f = type_config["damageF"]
            self.damage_i = type_config["damageI"]
            self.damage = self.damage_i
        self.range = type_config["range"]
        self.max_stability = type_config["stability"]
        self.cost = type_config["cost"]

    def attack(self, damage):

        if damage <= 0:
            return
        for encryption in self.encryption:
            if damage <= encryption:
                encryption -= damage
                self.stability -= damage
                return
            else:
                damage -= encryption
                self.stability -= encryption
                self.encryption.remove(encryption)

        self.actual_stability -= damage
        self.stability -= damage
        
    def encrypt(self, encryption):
        self.encryption.append(encryption)
        self.stability += encryption

    def decay(self):
        for encryption in self.encryption:
            if encryption >= 0.15:
                encryption -= 0.15
                self.stability -= 0.15
            else:
                self.stability -= encryption
                self.encryption.delete(self.encryption.index(encryption))

    def self_destruct(self):
        pass

    def __toString(self):
        owner = "Friendly" if self.player_index == 0 else "Enemy"
        removal = ", pending removal" if self.pending_removal else ""
        return "{} {}, stability: {} location: {}{} ".format(owner, self.unit_type, self.stability, [self.x, self.y], removal)

    def __str__(self):
        return self.__toString()

    def __repr__(self):
        return self.__toString()
    """
    def __cmp__(self, other):
        if self.id < other.id:
            return -1
        if self.id == other.id:
            return 0
        if self.id > other.id:
            return 1
    """

