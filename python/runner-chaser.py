import pygame
from abc import ABCMeta, abstractmethod
from time import sleep
from random import randint

def enum(*sequential, **named):
    """
    Enums in python!
    """
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)
    

class Character(object):
    
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

    score = 0
        
    def increase_score(self):
        self.score += 1
        
    def decrease_score(self):
        self.score -+ 1


class MovingCharacter(Character):

    max_moves_per_turn = 1
    
    class IllegalMove(Exception): pass
    
    def move(self, new_pos, grid):
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
            raise MovingCharacter.IllegalMove("Cannot move off the grid.")
        
        self.position = new_pos
        
    def move_up(self, grid, positions=1):
        self.move((self.position[0], self.position[1] - positions), grid)
        
    def move_down(self, grid, positions=1):
        self.move((self.position[0], self.position[1] + positions), grid)
        
    def move_left(self, grid, positions=1):
        self.move((self.position[0] - positions, self.position[1]), grid)
        
    def move_right(self, grid, positions=1):
        self.move((self.position[0] + positions, self.position[1]), grid)


class Runner(MovingCharacter, Score):
    pass
    

class Chaser(MovingCharacter, Score):
    pass
    
    
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

    def __init__(self, size):
        self.size = size
        
    def contains_coords(self, coords):
        """
        Checks whether the grid contains the given coordinates.
        """
        return (coords[0] < self.size[0] and coords[1] < self.size[1]) and \
            (coords[0] >= 0 and coords[1] >= 0)


class Game(object):

    class Lose(Exception): pass
    class Win(Exception): pass

    def __init__(self, grid_size, runner_start_pos, chaser_start_pos):
        self.grid = Grid(grid_size)
        self.runner = Runner(runner_start_pos, (0, 0, 255))
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
            self.apples.remove(apple)
            
        self.refill_apples()
        
        if self.runner.score >= 100:
            raise Game.Win("You ate 100 apples!")
        elif self.chaser.score >= 100:
            raise Game.Lose("The chaser ate 100 apples.")
        
        
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
    draw_character(window, game.runner)
    draw_character(window, game.chaser)
    for apple in game.apples:
        draw_character(window, apple)
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
    
#    while True:
#        try:
#            game.tick()
#        except Game.Win, e:
#            print "You won! %s" % e
#            break
#        except Game.Lose, e:
#            print "You lost. %s" % e
#            break
#            
#        draw_all(game, window)
#        print "Runner score: %d, Chaser score: %d" % (game.runner.score, game.chaser.score)
        #sleep(0.1)
    
    
    
    
