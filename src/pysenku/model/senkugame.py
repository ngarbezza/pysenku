'''
Created on 2009.01.14
Last Update on 2009.01.24
@author: Nahuel
'''

from pysenku.util.stack         import DynamicBoundedStack
from pysenku.util.observer      import Subject

# Max movements that you can undo.
# for infinite undo, just put a value > 32, because
# the game doesn't allow more of 32 movements.
MAX_UNDO_ACTIONS = 5

# Game tracking (control the game end)
# True to enable, False to disable
DEFAULT_GAME_TRACKING = True

#auxiliary function
def avg(a, b):
    '''Return a new tuple with average 
    of elements from a and b.'''
    
    res = []
    for i in range(len(a)):
        res.append((a[i] + b[i]) / 2)
    return tuple(res)

class SenkuGame(Subject):
    '''
    Implements all the Senku game logic.
    
    @ivar _board: Dictionary with the game board.
    @ivar _undo_stack: Stack of undo commands (movements).
    
    @note: This class use Subject as an interface (to notify changes).
    '''
    
    def __init__(self):
        '''Constructor of SenkuGame.'''
        
        Subject.__init__(self)
        self._board = {}
        self.__fill_board()
        self._undo_stack = DynamicBoundedStack(MAX_UNDO_ACTIONS)
        self._with_tracking = DEFAULT_GAME_TRACKING
    
    
    def get_board(self):
        '''Getter of _board.'''
        
        return self._board
    
    
    def get_undo_stack(self):
        '''Getter of _undo_stack.'''
        
        return self._undo_stack
    
    
    def set_tracking(self, track):
        '''Enable or disable the game tracking.'''
        
        self._with_tracking = track
    
    
    def __fill_board(self):
        '''Fill the entire board with True's except the center.'''
        
        for x in (0, 1, 5, 6):
            for y in (2, 3, 4):
                self.fill_cell((x, y))
        
        for x in (2, 3, 4):
            for y in range(7):
                self.fill_cell((x, y))
        
        self.empty_cell((3, 3))         # the center
    
    
    def fill_cell(self, cell):
        '''Mark a cell specified as fill.'''
        
        self.get_board()[cell] = True
        self.notify('CELL_ON', cell)
    
    
    def empty_cell(self, cell):
        '''Mark a cell specified as empty.'''
        
        self.get_board()[cell] = False
        self.notify('CELL_OFF', cell)
    
    
    def check_distance(self, orig, dest):
        '''Checks if the distance between the two points received
        is appropiate for a movement in the game.'''
        
        return                                                      \
            (abs(orig[0] - dest[0]) == 2 and orig[1] == dest[1])    \
                or                                                  \
            (abs(orig[1] - dest[1]) == 2 and orig[0] == dest[0])
    
    
    def check_cells(self, orig, dest):
        '''
        Checks the movement condition:
            +. origin is fill
            +. destination is empty
            +. the cell between orig and dest is fill
        '''
        
        return self.get_board()[orig] and not self.get_board()[dest] \
            and self.get_board()[avg(orig, dest)]
    
    
    def movement_done(self, command):
        '''A movement command was executed, then the game push
        this command, notify changes and control the end.'''
        
        self.get_undo_stack().push(command)
        self.notify('UNDO_STACK', self.get_undo_stack())
        if self._with_tracking:
            self.check_end()
    
    
    def undo(self):
        '''Undo the last action, if it's possible.'''
        
        self.get_undo_stack().pop().undo()
        self.notify('UNDO_STACK', self.get_undo_stack())
    
    
    def check_end(self):
        '''Check if there's no possible movements, then notify
        if the game is over.'''
        
        cells_left = 0
        for pos1, cell in self.get_board().items():
            if cell:
                for pos2 in self.get_board():
                    if self.check_distance(pos1, pos2) \
                    and self.check_cells(pos1, pos2):
                        return None         # movement
                cells_left += 1
        self.notify('GAME_OVER', cells_left)
    
    
    def get_all_changes(self):
        '''Force to trigger all the model changes to update its observers.'''

        self.notify('UNDO_STACK', self.get_undo_stack())
        for k in self.get_board():
            if self.get_board()[k]:
                self.notify('CELL_ON', k)
            else:
                self.notify('CELL_OFF', k)
    
    
    def restart(self):
        '''Reset the game (starting a new game too).'''
        
        self.__fill_board()
        self.get_undo_stack().make_empty()
        self.notify('UNDO_STACK', self.get_undo_stack())
