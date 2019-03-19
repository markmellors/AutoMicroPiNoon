from enum import Enum


class State(Enum):
    #state enumeration
    STOPPED = 0
    OFFLINE = 1
    RC = 2
    SUPERVISOR = 3
    AUTO = 4

class Colour(Enum):
    BLUE = 1
    RED = 2
    GREEN = 3
    CYAN = 4
    MAGENTA = 5
    YELLOW = 6
    BLACK = 7
