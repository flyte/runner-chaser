import pygame
from abc import ABCMeta, abstractmethod
from time import sleep
from random import randint, choice
from math import ceil
from numpy import interp
from pprint import pprint
from events import Event

def enum(*sequential, **named):
    """
    Enums in python!
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
    
def log(msg):
    print "Log: %s" % msg
    
class Character(object):
    """
    Abstract base class for all characters on the grid.
    """
    
    __metaclass__ = ABCMeta
    
    def __init__(self, position, colour):
        """
        Parameters:
        position:
            Tuple (x, y) depicting coordinates of character.
        colour:
            Tuple (255, 0, 127) depicting RGB colour values.
        """
        self.position = position
        self.colour = colour
        
        
class Score(object):
    """
    Score mixin class for characters which keep a score.
    """

    score = 0
        
    def increase_score(self):
        self.score += 1
        
    def decrease_score(self):
        self.score -+ 1


class MovingCharacter(Character):
    """
    Base class for a character which has the ability to move.
    """
    
    __metaclass__ = ABCMeta
    
    class IllegalMove(Exception): pass
    
    def __init__(self, position, colour, max_moves_per_turn=1):
        super(MovingCharacter, self).__init__(position, colour)
        self.max_moves_per_turn = max_moves_per_turn
    
    def move(self, new_pos, grid):
        """
        Move the character on the grid.
        """
        x_diff = abs(self.position[0] - new_pos[0])
        y_diff = abs(self.position[1] - new_pos[1])
        
        if x_diff and y_diff:
            raise MovingCharacter.IllegalMove("Cannot move in two directions in one turn.")
        elif x_diff > self.max_moves_per_turn or y_diff > self.max_moves_per_turn:
            tried = x_diff if x_diff > y_diff else y_diff
            raise MovingCharacter.IllegalMove(
                "Cannot move more than %d moves in one turn (you tried %d moves)." % (
                    self.max_moves_per_turn, tried))
        elif not grid.contains_coords(new_pos):
            raise MovingCharacter.IllegalMove("Cannot move off the grid. %s at %d, %d tried to" \
                " move to %d, %d" % (
                self.__class__.__name__, self.position[0],
                self.position[1], new_pos[0], new_pos[1])
            )
        
        self.position = new_pos
        
    def move_up(self, grid, positions=1):
        self.move((self.position[0], self.position[1] - positions), grid)
        
    def move_down(self, grid, positions=1):
        self.move((self.position[0], self.position[1] + positions), grid)
        
    def move_left(self, grid, positions=1):
        self.move((self.position[0] - positions, self.position[1]), grid)
        
    def move_right(self, grid, positions=1):
        self.move((self.position[0] + positions, self.position[1]), grid)
        
    def move_noop(self, grid, positions=1):
        pass


class Runner(MovingCharacter, Score):
    carnivorous = False
    

class Chaser(MovingCharacter, Score):
    carnivorous = True
    
    
class Apple(Character):
    
    def __init__(self, position, shelf_life=160):
        super(Apple, self).__init__(position, (0, 255, 0))
        self.shelf_life = shelf_life
        
    def decrease_shelf_life(self):
        self.shelf_life -= 1
    
    
class Wall(Character):
    
    Orientation = enum("HORIZONTAL", "VERTICAL")
    
    def __init__(self, position, orientation):
        super(Wall, self).__init__(position)
        self.orientation = orientation
        
        
class Grid(object):

    Direction = enum("NORTH", "EAST", "SOUTH", "WEST")

    def __init__(self, size):
        self.size = size
        
    def contains_coords(self, coords):
        """
        Checks whether the grid contains the given coordinates.
        """
        return (coords[0] < self.size[0] and coords[1] < self.size[1]) and \
            (coords[0] >= 0 and coords[1] >= 0)
            
    def distance_to_wall(self, coords):
        """
        Returns the distance between coords and the nearest wall and the direction it's in.
        """
        directions = [
            (Grid.Direction.NORTH, coords[1]),
            (Grid.Direction.EAST, self.size[0]- 1 - coords[0]),
            (Grid.Direction.SOUTH, self.size[1] - 1 - coords[1]),
            (Grid.Direction.WEST, coords[0])
        ]
        return sorted(directions, key=lambda d: d[1])[0]
        
    def surrounding_valid_coords(self, coords, radius=1, avoid_set=set()):
        """
        Returns all valid coordinates in a straight line within the given radius.
        """
        for i in WALLS:
            avoid_set.add(i)
        
        valid_coords = []
        for i in xrange(radius):
            functions = (
                lambda c: (c[0] + 1 + i, c[1]),
                lambda c: (c[0] - (1 + i), c[1]),
                lambda c: (c[0], c[1] + 1 + i),
                lambda c: (c[0], c[1] - (1 + i))
            )
            for f in functions:
                c = f(coords)
                if self.contains_coords(c) and c not in avoid_set:
                    valid_coords.append(c)
                    
        return valid_coords
    
    @staticmethod
    def distance(a, b, moves_per_turn=1):
        """
        Calculates the amount of moves required to get from a to b.
        """
        xdiff = abs(a[0] - b[0])
        ydiff = abs(a[1] - b[1])
        return ceil(float(xdiff + ydiff) / float(moves_per_turn))
        
    @staticmethod
    def direction(a, b):
        """
        Calculates which direction b is from a. Returns a Grid.Direction.
        """
        xdiff = a[0] - b[0]
        ydiff = a[1] - b[1]
        
        direction = [None, None]
        if xdiff >= ydiff:
            # It's east or west
            if xdiff >= 0:
                direction[0] = Grid.Direction.WEST
            else:
                direction[0] = Grid.Direction.EAST
            # Secondary direction
            if ydiff >= 0:
                direction[1] = Grid.Direction.NORTH
            elif ydiff < 0:
                direction[1] = Grid.Direction.SOUTH
        else:
            # It's north or south
            if ydiff >= 0:
                direction[0] = Grid.Direction.NORTH
            else:
                direction[0] = Grid.Direction.SOUTH
            # Secondary direction
            if xdiff >= 0:
                direction[1] = Grid.Direction.WEST
            elif xdiff < 0:
                direction[1] = Grid.Direction.EAST
        
        return tuple(direction)
    
    @staticmethod
    def coords_for_direction(a, direction, steps=1):
        """
        Calculates coordinates for moving in the specified Grid.Direction from a.
        """
        if direction == Grid.Direction.NORTH:
            return (a[0], a[1] - steps)
        elif direction == Grid.Direction.EAST:
            return (a[0] + steps, a[1])
        elif direction == Grid.Direction.SOUTH:
            return (a[0], a[1] + steps)
        elif direction == Grid.Direction.WEST:
            return (a[0] - steps, a[1])
            
    @staticmethod
    def opposite_direction(direction):
        """
        Calculates the opposite direction to the one provided.
        """
        if direction == Grid.Direction.NORTH:
            return Grid.Direction.SOUTH
        elif direction == Grid.Direction.EAST:
            return Grid.Direction.WEST
        elif direction == Grid.Direction.SOUTH:
            return Grid.Direction.NORTH
        elif direction == Grid.Direction.WEST:
            return Grid.Direction.EAST
            
    @staticmethod
    def next_pos(a, b, max_moves_per_turn=1):
        """
        Calculates the next move from a to b as the crow flies and returns the coordinates.
        """
        target_x, target_y = b
        my_x, my_y = a
        pos = list(a)
        
        diff_x = abs(my_x - target_x)
        diff_y = abs(my_y - target_y)
        
        # Move y first if they're equal
        if diff_y >= diff_x:
            moves = diff_y if max_moves_per_turn > diff_y else max_moves_per_turn

            # Move down
            if my_y < target_y: pos[1] += moves
            # Move up
            else: pos[1] -= moves
        else:
            moves = diff_x if max_moves_per_turn > diff_x else max_moves_per_turn
            
            # Move right
            if my_x < target_x: pos[0] += moves
            # Move left
            else: pos[0] -= moves
        
        return tuple(pos)


class Game(object):

    class Lose(Exception): pass
    class Win(Exception): pass

    def __init__(self, grid_size, runner_start_pos, chaser_start_pos, win_score=100):
        self.grid = Grid(grid_size)
        self.runner = Runner(runner_start_pos, (0, 0, 255), 2)
        self.chaser = Chaser(chaser_start_pos, (255, 0, 0))
        self.apples = []
        self.refill_apples()
        self.wall = None
        self.win_score = win_score
        
    def __random_coords(self):
        return (randint(0, self.grid.size[0] - 1),
            randint(0, self.grid.size[1] - 1))
        
    def refill_apples(self):
        while len(self.apples) < APPLE_COUNT:
            coords = self.__random_coords()
            if coords not in WALLS:
                self.apples.append(Apple(coords))
        
    def tick(self):
        if self.chaser.position == self.runner.position:
            raise Game.Lose("The runner was caught by the chaser.")
        
        eaten_apples = []
        for apple in self.apples:
            if self.runner.position == apple.position:
                self.runner.increase_score()
                eaten_apples.append(apple)
            elif self.chaser.position == apple.position:
                self.chaser.increase_score()
                eaten_apples.append(apple)
            apple.decrease_shelf_life()
            if apple.shelf_life < 0:
                eaten_apples.append(apple)
        
        for apple in eaten_apples:
            # Sometimes both the runner and the chaser are on the same apple, so they appear in
            # eaten_apples twice.
            if apple in self.apples:
                self.apples.remove(apple)
            
        self.refill_apples()
        
        if self.runner.score >= self.win_score:
            raise Game.Win("You ate %d apples!" % self.win_score)
        elif self.chaser.score >= self.win_score:
            raise Game.Lose("The chaser ate %d apples." % self.win_score)
        

class AStarNode(object):

    def __init__(self, pos, g, h):
        self.pos = pos
        self.f = g + h
        self.g = g
        self.h = h
        
    def __repr__(self):
        return "Pos(%d,%d), F(%d), G(%d), H(%d)" % (
            self.pos[0], self.pos[1], self.f, self.g, self.h)


class Player(object):

    __metaclass__ = ABCMeta

    def __init__(self, game):
        self.game = game
        self.path = None
        self.path_progress = 0
        self.avoid_set = set()
        self.path_interruptions = [self.target_gone]
        self.path_found = Event()
        self.successors_evaluated = Event()
        self.target_character = None

    def viable_apples(self):
        # Find the distances to the apples
        # Disregard any apples we can't get to in time
        ## Give them a score based on how close/far they are from the other player?
        ## The further the better for the runner, the closer the better for the chaser.
        viable_apples = []
        for apple in game.apples:
            distance = Grid.distance(self.character.position, apple.position,
                self.character.max_moves_per_turn)
            if distance <= apple.shelf_life:
                viable_apples.append({ "apple": apple, "distance": distance })
        
        return sorted(viable_apples, key=lambda a: a["distance"])

    def target_gone(self):
        if len(self.path) > 1:
            return self.path[len(self.path) - 1].pos != self.target_character.position

    def interrupt_path(self):
        for i in self.path_interruptions:
            if i():
                return True

        return False
        
    def make_move(self):
        target_coords = self.find_target_coords()

        if not target_coords:
            self.character.move_noop(self.game.grid)
            return

        path = self.find_path(target_coords)
        next_move = path[1].pos if len(path) > 1 else path[0].pos
        
        self.character.move(next_move, self.game.grid)

        #self.character.move(
        #    Grid.next_pos(self.character.position, target_coords,
        #        self.character.max_moves_per_turn),
        #        self.game.grid)

    def heuristic_distance(self, target_coords, from_coords=None):
        """
        Estimates distance cost from current location to target. @TODO: Add cost for proximity to
        chaser and walls.
        """
        if not from_coords: from_coords = self.character.position
        
        distance = Grid.distance(from_coords, target_coords)
        
        cost = 0
        pos = list(from_coords)
        while tuple(pos) != target_coords:
            cost += 1
            pos = Grid.next_pos(pos, target_coords, self.character.max_moves_per_turn)
        
        return cost

    def create_a_star_node(self, nc, pos, target_coords):
        return AStarNode(pos,
            Grid.distance(nc.pos, pos,
                self.character.max_moves_per_turn) + nc.g,
            self.heuristic_distance(target_coords, pos)
        )

    def find_path(self, target_coords):
        """
        Use A* algorithm to plot the path with the least cost from the current position
        to the target (apple).
        Returns list of AStarNode starting with the current position and ending with
        the target position.
        """
        self.path_progress += 1
        if self.path and self.path_progress < len(self.path) and not self.interrupt_path():
            return self.path[self.path_progress:]
        
        if not target_coords:
            return [AStarNode(self.character.position, 0, 0)]
        
        # Add the current position to open_set
        start_node = AStarNode(self.character.position, 0, self.heuristic_distance(target_coords))
        open_set = { start_node.pos: start_node }
        closed_set = {}
        came_from = {}
        
        while len(open_set):
            # Get the node from open_set which has the least amount of total cost (f)
            sorted_open_set = sorted(open_set.iteritems(), key=lambda n: n[1].f)
            nc = sorted_open_set[0][1]
            
            # Remove the current node from open_set and add it to closed_set
            del open_set[nc.pos]
            closed_set[nc.pos] = nc
            
            # Get list of surrounding valid coordinates for the current node and create AStarNode
            # instances for each
            node_successors = [self.create_a_star_node(nc, pos, target_coords) for pos in \
                self.game.grid.surrounding_valid_coords(nc.pos,
                    self.character.max_moves_per_turn, self.avoid_set)]
            
            # For each of the nodes surrounding the current node
            for ns in node_successors:
                # If we've evaluated this neighbor node before and it took the same or more
                # cost to get to it this time then move on.
                in_closed_set = ns.pos in closed_set
                if in_closed_set and ns.g >= closed_set[ns.pos].g:
                    continue
                if ns.pos in open_set and ns.g >= open_set[ns.pos].g:
                    continue
                
                if in_closed_set: del closed_set[ns.pos]
 
                # Set the current node as the originating node for this coordinate
                came_from[ns.pos] = nc
                
                # If we've reached our goal, reconstruct the path and return it
                if ns.pos == target_coords:
                    self.path = self.reconstruct_path(came_from, ns)
                    self.path_progress = 0
                    #Fire event
                    self.path_found(self.path)
                    return self.path
                
                # List this neighbor for evaluation
                open_set[ns.pos] = ns
            
            # Fire event
            self.successors_evaluated(open_set, closed_set, self.character.position, target_coords)
        
        # We didn't reach our goal, so return our current position only
        return [start_node]
        
    def reconstruct_path(self, came_from, nc):
        """
        Recursive function to build a list of coordinates from target, back to character.position
        """
        if nc.pos in came_from:
            return self.reconstruct_path(came_from, came_from[nc.pos]) + [nc]
        else:
            return [nc]

    @abstractmethod
    def find_target_coords(self):
        pass


class ChaserPlayer(Player):

    def __init__(self, game):
        super(ChaserPlayer, self).__init__(game)
        self.character = game.chaser

    def find_target_coords(self):
        viable_apples = self.viable_apples()
        target_coords = None
        self.target_character = None
    
        # Target the runner
        target_coords = self.game.runner.position
        self.target_character = self.game.runner
        
        # Unless an apple is closer
        if len(viable_apples):
            runner_distance = Grid.distance(self.character.position, self.game.runner.position)
            if viable_apples[0]["distance"] < runner_distance:
                target_coords = viable_apples[0]["apple"].position
                self.target_character = viable_apples[0]["apple"]
        
        return target_coords
        

class RunnerPlayer(Player):

    def __init__(self, game, chaser_danger_zone=3):
        super(RunnerPlayer, self).__init__(game)
        self.character = game.runner
        self.window = window
        self.chaser_danger_zone = chaser_danger_zone
        self.path_interruptions.append(self.in_danger_zone)

    def in_danger_zone(self):
        """
        Returns distance to chaser if our character is in the danger zone, else returns 0
        """
        chaser_distance = Grid.distance(self.character.position, self.game.chaser.position)
        if chaser_distance <= self.chaser_danger_zone:
            return chaser_distance
        else:
            return 0
        
    def find_target_coords(self):
        viable_apples = self.viable_apples()
        target_coords = None
        self.target_coords = None

        # Get a list of all valid coordinates surrounding the chaser so we can avoid it
        self.avoid_set = set(self.game.grid.surrounding_valid_coords(
            self.game.chaser.position, 2))

        if len(viable_apples):
            target_coords = viable_apples[0]["apple"].position
            self.target_character = viable_apples[0]["apple"]
        
        return target_coords

     
GRID_POINT_DISTANCE = 10
APPLE_COUNT = 2
WALLS = []
DRAW_OPEN_SET = False
DRAW_CLOSED_SET = False
DRAW_PATH = False

def get_position(grid_coords):
    """
    Takes grid coords and returns an (x, y) tuple of the on-screen coords.
    """
    x = (grid_coords[0] + 1) * GRID_POINT_DISTANCE
    y = (grid_coords[1] + 1) * GRID_POINT_DISTANCE
    return (x, y)

def draw_grid(game, window):
    s = game.grid.size
    d = GRID_POINT_DISTANCE
    
    window.fill((0, 0, 0))
    ix = 0
    for x in xrange(s[0]):
        iy = 0
        for y in xrange(s[1]):
            if (ix, iy) in WALLS:
                pos = get_position((ix, iy))
                pygame.draw.rect(window, (255, 255, 255), pygame.Rect(pos[0], pos[1], 3, 3))
            else:
                pygame.draw.circle(window, (40, 40, 40), get_position((ix, iy)), 1)
            iy += 1
        ix += 1

def draw_character(window, character):
    pygame.draw.circle(window, character.colour, get_position(character.position), 10)
    
def draw_path(path):
    if DRAW_PATH:
        # Fill in path
        for node in path:
            pygame.draw.circle(window, (0, 0, 255), get_position(node.pos), 3)
        pygame.display.flip()
    
def draw_sets(open_set, closed_set, character_position, target_coords):
    if DRAW_OPEN_SET:
        for coords, node in open_set.iteritems():
            if coords == character_position:
                continue
            pygame.draw.circle(window, (255, 255, 255), get_position(coords), 3, 1)

    if DRAW_CLOSED_SET:
        # Fill in closed set
        for coords, node in closed_set.iteritems():
            if coords == character_position:
                continue
            red = interp(node.h, (0, Grid.distance(character_position, target_coords)), (0, 255))
            #red = 255
            pygame.draw.circle(window, (red, 255 - red, 0), get_position(coords), 5)
        pygame.display.flip()

def draw_all(game, window):
    draw_grid(game, window)
    for apple in game.apples:
        draw_character(window, apple)
    draw_character(window, game.runner)
    draw_character(window, game.chaser)
    pygame.display.flip()

if __name__ == "__main__":
    grid_size = (80, 45)
    runner_start_pos = (0, grid_size[1] - 1)
    chaser_start_pos = (grid_size[0] - 1, 0)

    for i in xrange(grid_size[1]):
        x = grid_size[0] / 2
        if i != grid_size[1] / 2:
            WALLS.append((x, i))
            WALLS.append((x - 1, i))


    game = Game(grid_size, runner_start_pos, chaser_start_pos, 100)
    
    pygame.init()
    window = pygame.display.set_mode((
        GRID_POINT_DISTANCE * (grid_size[0] + 1),
        GRID_POINT_DISTANCE * (grid_size[1] + 1)))
    
    draw_all(game, window)
    
    p_runner = RunnerPlayer(game)
    p_chaser = ChaserPlayer(game)
    
    p_runner.path_found += draw_path
    p_runner.successors_evaluated += draw_sets
    
    previous_scores = [0, 0]
    while True:
        for c in [ p_runner, p_chaser ]:
            c.make_move()

        try:
            game.tick()
        except Game.Win, e:
            print "Runner won! %s" % e
            break
        except Game.Lose, e:
            print "Chaser won! %s" % e
            break
            
        draw_all(game, window)
        if game.runner.score != previous_scores[0] or game.chaser.score != previous_scores[1]:
            print "Runner score: %d, Chaser score: %d" % (game.runner.score, game.chaser.score)
            previous_scores = [ game.runner.score, game.chaser.score ]
        #sleep(0.25)
    
    draw_all(game, window)
