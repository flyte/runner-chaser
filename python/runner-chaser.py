import pygame
from abc import ABCMeta, abstractmethod
from time import sleep
from random import randint, choice
from math import ceil

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
            raise MovingCharacter.IllegalMove("Cannot move off the grid. %s at %d, %d tried to move to %d, %d" % (
                self.__class__.__name__, self.position[0], self.position[1], new_pos[0], new_pos[1]))
        
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
    
    def __init__(self, position, shelf_life=8):
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
        Calculates the next move from a to b and returns the coordinates.
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

    def __init__(self, grid_size, runner_start_pos, chaser_start_pos):
        self.grid = Grid(grid_size)
        self.runner = Runner(runner_start_pos, (0, 0, 255), 2)
        self.chaser = Chaser(chaser_start_pos, (255, 0, 0))
        self.apples = []
        self.refill_apples()
        self.wall = None
        
    def __random_coords(self):
        return (randint(0, self.grid.size[0] - 1),
            randint(0, self.grid.size[1] - 1))
        
    def refill_apples(self):
        while len(self.apples) < APPLE_COUNT:
            self.apples.append(Apple(self.__random_coords()))
        
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
        
        if self.runner.score >= 100:
            raise Game.Win("You ate 100 apples!")
        elif self.chaser.score >= 100:
            raise Game.Lose("The chaser ate 100 apples.")
        

class Player(object):

    __metaclass__ = ABCMeta

    def __init__(self, game):
        self.game = game
        
    def viable_apples(self):
        # Find the distances to the apples
        # Disregard any apples we can't get to in time
        ## Give them a score based on how close/far they are from the other player?
        ## The further the better for the runner, the closer the better for the chaser.
        viable_apples = []
        for apple in game.apples:
            distance = Grid.distance(self.character.position, apple.position, self.character.max_moves_per_turn)
            if distance <= apple.shelf_life:
                viable_apples.append({ "apple": apple, "distance": distance })
        
        return sorted(viable_apples, key=lambda a: a["distance"])
        
    def make_move(self):
        target_coords = self.find_target_coords()
        
        if not target_coords:
            self.character.move_noop(self.game.grid)
            return
        
        self.character.move(
            Grid.next_pos(self.character.position, target_coords, self.character.max_moves_per_turn),
                self.game.grid)

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
    
        # Target the runner
        target_coords = self.game.runner.position
        
        # Unless an apple is closer
        if len(viable_apples):
            runner_distance = Grid.distance(self.character.position, self.game.runner.position)
            if viable_apples[0]["distance"] < runner_distance:
                target_coords = viable_apples[0]["apple"].position
                
        return target_coords
        

class RunnerPlayer(Player):

    def __init__(self, game):
        super(RunnerPlayer, self).__init__(game)
        self.character = game.runner

    def heuristic_distance(self, target_coords):
        """
        Estimates distance cost from current location to target. Adds cost for proximity to chaser and walls.
        """
        chaser_pos = self.game.chaser.position
        distance = Grid.distance(self.character.position, target_coords)
        danger_zone = 3
        
        cost = 0
        pos = list(self.character.position)
        while tuple(pos) != target_coords:
            cost += 1
            pos = Grid.next_pos(pos, target_coords, self.character.max_moves_per_turn)
            
            # If pos in the danger zone, add some cost
            chaser_distance = Grid.distance(pos, self.game.chaser.position, 1)
            if chaser_distance <= danger_zone:
                cost += int(danger_zone - chaser_distance + 1)
                
        return cost

    def find_target_coords(self):
        viable_apples = self.viable_apples()
        target_coords = None

        if len(viable_apples):
            target_coords = viable_apples[0]["apple"].position
            
        chaser_distance = Grid.distance(self.character.position, self.game.chaser.position, 1)
        danger_zone = 3
        
        if chaser_distance <= danger_zone:
            log("Chaser is in danger zone!")
            pos = self.character.position
            moves = self.character.max_moves_per_turn
            direction = Grid.direction(pos, self.game.chaser.position)
            N, E, S, W = (Grid.Direction.NORTH, Grid.Direction.EAST,
                Grid.Direction.SOUTH, Grid.Direction.WEST)
            
            target_coords = Grid.coords_for_direction(
                pos, Grid.opposite_direction(direction[0]), moves)
                
            log("Trying to move in the %s direction.." % Grid.opposite_direction(direction[0]))
            
            if not self.game.grid.contains_coords(target_coords):
                log("My evasive action takes me out of the grid (%d, %d).." % (
                    target_coords[0], target_coords[1]))
                # If the chaser is inline with us
                if not direction[1]:
                    log("Chaser is inline with us")
                    if direction[0] in (N, S):
                        log("Chaser is primarily north or south")
                        middle = self.game.grid.size[0] / 2.0
                        
                        # If we're in the middle
                        if pos[0] == middle:
                            log("We're in the middle of the grid on the x plane")
                            # Choose a direction at random
                            new_direction = choice((E, W))
                        else:
                            log("We're in the east or west half of the grid")
                            # If we're in the east half, go west (where the skies are blue), else east
                            new_direction = W if pos[0] > middle else E
                    else: # Direction was east or west, so we go north or south
                        middle = self.game.grid.size[1] / 2.0
                        
                        if pos[1] == middle:
                            log("We're in the middle of the grid on the y plane")
                            new_direction = choice((N, S))
                        else:
                            log("We're in the north or south half of the grid")
                            new_direction = N if pos[1] > middle else S
                else:
                    # We go in the direction that the chaser isn't
                    new_direction = Grid.opposite_direction(direction[1])
                    log("Going in the direction that the chaser isn't (%s).." % new_direction)
            
                target_coords = Grid.coords_for_direction(pos, new_direction, moves)
            
            # If our evasive action still takes us off the grid
            if not self.game.grid.contains_coords(target_coords):
                log("My evasive action takes me out of the grid again (%d, %d).." % (
                    target_coords[0], target_coords[1]))
                log("Last resort. Going in the direction that the chaser is furthest in (%s)" % direction[1])
                # We go in the direction the chaser is furthest in
                target_coords = Grid.coords_for_direction(pos, direction[0], moves)

        return target_coords

     
GRID_POINT_DISTANCE = 50
APPLE_COUNT = 2

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
            pygame.draw.circle(window, (255, 255, 255), get_position((ix, iy)), 3)
            iy += 1
        ix += 1

def draw_character(window, character):
    pygame.draw.circle(window, character.colour, get_position(character.position), 10)
    
def draw_all(game, window):
    draw_grid(game, window)
    for apple in game.apples:
        draw_character(window, apple)
    draw_character(window, game.runner)
    draw_character(window, game.chaser)
    pygame.display.flip()

if __name__ == "__main__":
    grid_size = (16, 9)
    runner_start_pos = (0, grid_size[1] - 1)
    chaser_start_pos = (grid_size[0] - 1, 0)
    
    game = Game(grid_size, runner_start_pos, chaser_start_pos)
    
    pygame.init()
    window = pygame.display.set_mode((
        GRID_POINT_DISTANCE * (grid_size[0] + 1),
        GRID_POINT_DISTANCE * (grid_size[1] + 1)))
    
    draw_all(game, window)
    
    p_runner = RunnerPlayer(game)
    p_chaser = ChaserPlayer(game)
    
    previous_scores = [0, 0]
    while True:
        for c in [ p_runner, p_chaser ]:
            c.make_move()

        try:
            game.tick()
        except Game.Win, e:
            print "You won! %s" % e
            break
        except Game.Lose, e:
            print "You lost. %s" % e
            break
            
        draw_all(game, window)
        if game.runner.score != previous_scores[0] or game.chaser.score != previous_scores[1]:
            print "Runner score: %d, Chaser score: %d" % (game.runner.score, game.chaser.score)
            previous_scores = [ game.runner.score, game.chaser.score ]
        sleep(0.1)
    
    draw_all(game, window)
    
    
    
