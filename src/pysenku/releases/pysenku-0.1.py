##############################################################################
#
# pysenku - A Python implementation of the classic "Senku" game
# Copyright (C) 2010 Nahuel Garbezza (n.garbezza@gmail.com)
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
# USA
#
# http://code.google.com/p/pysenku/
#
##############################################################################

__version__ = '0.1'
__author__ = 'Nahuel Garbezza'
__copyright__ = "Copyright (C) 2010 Nahuel Garbezza"
__license__ = "gpl"
__email__ = 'n.garbezza@gmail.com'

from tkinter import *

##############################################################################
# UTILITIES - STACK
##############################################################################

class Stack(object):
    '''
    Stack data structure.
    
    @ivar _data: Internal storage (list).
    '''

    def __init__(self):
        '''Constructor of Stack.'''
        
        self._data = []
    
    
    def push(self, elem):
        '''Add a element to the stack.'''
        
        self._data.append(elem)
    
    
    def pop(self):
        '''Remove the stack's top element and returns it.'''
        
        return self._data.pop()
    
    
    def is_empty(self):
        '''Check if the stack is empty.'''
        
        return not self._data

    
    def make_empty(self):
        '''Remove all elements.'''
        
        self._data = []


class BoundedStack(Stack):
    '''
    A Stack with a limit of elements.
    
    @ivar _size: max size.
    '''
    
    def __init__(self, size):
        '''Constructor of BoundedStack.'''
        
        super().__init__()
        self._size = size
    
        
    def is_full(self):
        '''Check if the stack is full (reached the max size).'''
        
        return len(self._data) == self._size
    
    
    def can_push(self):
        '''Check if it's possible to push.'''
        
        return not self.is_full()
    
    
    def push(self, elem):
        '''Overrides the definition in Stack. If isn't possible
        to push, the method doesn't anything.'''
        
        if self.can_push():
            super().push(elem)


class DynamicBoundedStack(BoundedStack):
    '''Same as BoundedStack, but push() works different.'''
    
    def __init__(self, size):
        super().__init__(size)

    
    def can_push(self):
        '''Here is True.'''
        
        return True

    
    def push(self, elem):
        '''Always put the element, but if the stack reach
        the limit, removes the oldest element.'''
        
        if self.is_full():
            self._data.pop(0)       # the first element pushed (oldest)
        
        super().push(elem)

##############################################################################
# UTILITIES - OBSERVER
##############################################################################

class Subject(object):
    '''
    Interface to the observer pattern. All objects that notify
    changes must implement this interface.
    
    @ivar observers: Dictionary of <aspect, list of observers>
        for the object.
    '''
    
    def __init__(self):
        '''Initialize the observers' dictionary, with the
        special aspect "all".'''

        self.observers = {'all':[]}

    
    def add_observer(self, obj, aspect=None):
        '''Add a observer to the subject for an aspect specified.
        If you don't give an aspect, the object will be observer
        for all the subject's aspects.'''
        
        
        if aspect is None:
            self.observers['all'].append(obj)
        else:
            if aspect not in self.observers:              
                self.add_aspect(aspect)
            self.observers[aspect].append(obj)
    
    
    def remove_observer(self, obj, aspect=None):
        '''Remove an observer for an aspect.'''
        
        if aspect is None:
            self.observers['all'].remove(obj)
        else:
            self.observers[aspect].remove(obj)
    

    def notify(self, aspect, value):
        '''Notify changes for an aspect.'''
        
        for observer in self.observers[aspect]:
            observer.update(aspect, value)
        #also notify the observer in 'all' aspects
        for observer in self.observers['all']:
            observer.update(aspect, value)
    
    
    def add_aspect(self, aspect):
        '''Add the entry for an aspect (with an empty list).'''
        
        self.observers[aspect] = []


class Observer(object):
    '''Interface to the observer pattern. Represent 
    observers of subject's aspects.'''
    
    def update(self, aspect, value):
        '''The observers must override this method.'''
        
        pass


##############################################################################
# GAME LOGIC
##############################################################################

# Max movements that you can undo.
# for infinite undo, just put a value > 32, because
# the game doesn't allow more of 32 movements.
MAX_UNDO_ACTIONS = 5

class SenkuGame(Subject):
    '''
    Implements all the Senku game logic.
    
    @ivar _board: Dictionary with the game board.
    @ivar _undo_stack: Stack of undo commands (movements).
    
    @note: This class use Subject as an interface (to notify changes).
    '''
    
    def __init__(self):
        '''Constructor of SenkuGame.'''
        
        super().__init__()
        self._board = {}
        self.add_aspect('CELL_ON')
        self.add_aspect('CELL_OFF')
        self.add_aspect('UNDO_STACK')
        self.__fill_board()
        self._undo_stack = DynamicBoundedStack(MAX_UNDO_ACTIONS)
       
        
    def __fill_board(self):
        '''Fill the entire board with True's except the center.'''
        
        for i in (0, 1, 5, 6):
            for j in (2, 3, 4):
                self.fill_cell((i, j))
        for i in (2, 3, 4):
            for j in range(7):
                self.fill_cell((i, j))
        self.empty_cell((3, 3))         # the center
    
    
    def get_board(self):
        '''Getter of _board.'''
        
        return self._board    
    
    
    def fill_cell(self, cell):
        '''Mark a cell specified as fill.'''
        
        self._board[cell] = True
        self.notify('CELL_ON', cell)
    
    
    def empty_cell(self, cell):
        '''Mark a cell specified as empty.'''
        
        self._board[cell] = False
        self.notify('CELL_OFF', cell)
    
    
    def move(self, orig, dest):
        '''Receive two tuples and make the movement from origin to 
        destination, if it's possible. Also add a UndoAction to the stack.'''
        
        if self.__check_dist(orig, dest) and self.__check_cells(orig, dest):
            self.fill_cell(dest)
            self.empty_cell(orig)
            self.empty_cell(self.medium_cell(orig, dest))
            self._undo_stack.push(UndoAction(self, orig, dest))
            self.notify('UNDO_STACK', self._undo_stack)
    
    
    def medium_cell(self, a, b):
        '''Return the cell between a and b.'''
        
        return ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
    
    
    def __check_dist(self, orig, dest):
        '''Checks if the distance between the two points received
        is appropiate for a movement in the game.'''
        
        return                                                      \
            (abs(orig[0] - dest[0]) == 2 and orig[1] == dest[1])    \
                or                                                  \
            (abs(orig[1] - dest[1]) == 2 and orig[0] == dest[0])
    
    
    def __check_cells(self, orig, dest):
        '''
        Checks the movement condition:
            +. origin is fill
            +. destination is empty
            +. the cell between orig and dest is fill
        '''
        
        return self._board[orig] and not self._board[dest]          \
            and self._board[self.medium_cell(orig, dest)]
    
    
    def undo(self):
        '''Undo the last action, if it's possible.'''
        
        self._undo_stack.pop().undo()
        self.notify('UNDO_STACK', self._undo_stack)


    def get_all_changes(self):
        '''Force to trigger all the model changes to update its observers.'''

        self.notify('UNDO_STACK', self._undo_stack)
        for k in self._board:
            if self._board[k]:
                self.notify('CELL_ON', k)
            else:
                self.notify('CELL_OFF', k)
    
    
    def restart(self):
        '''Reset the game (starting a new game too).'''
        
        self.__fill_board()
        self._undo_stack.make_empty()
        self.notify('UNDO_STACK', self._undo_stack)


class UndoAction(object):
    '''
    A command for undo Senku moves.

    @ivar _game: The senku game.
    @ivar _origin: The move's origin position.
    @ivar _dest: The move's destination position.
    '''

    def __init__(self, game, orig, dest):
        '''Constructor of UndoAction.'''
        
        self._game = game
        self._origin = orig
        self._dest = dest
    
    
    def get_game(self):
        return self._game

    
    def get_origin(self):
        return self._origin

    
    def get_dest(self):
        return self._dest
    
    
    def undo(self):
        '''Perform the undo action, inverted movement.'''
        
        self._game.fill_cell(self._origin)
        self._game.fill_cell(self._game.medium_cell(self._origin, self._dest))
        self._game.empty_cell(self._dest)


##############################################################################
# GRAPHICAL USER INTERFACE
##############################################################################

BOARD_RECTANGLE_SIZE = 40
DIAMETER = 30 
DIST = BOARD_RECTANGLE_SIZE - DIAMETER

# board background color
BOARD_BG_COLOR = '#00B000'      #dark green
# selection color
BOARD_SEL_COLOR = 'green'

CELL_EMPTY_COLOR = 'black'
CELL_NOT_EMPTY_COLOR = 'red'


class UISenku(object):
    '''
    Implements the Graphical User Interface to the Senku.
    
    @ivar _game: the game logic (the model).
    @ivar _root: the main window.
    '''

    def __init__(self, game):
        '''Constructor of UISenku. Build the main window and the
        main frame.'''

        self._game = game
        self._root = Tk()
        self._root.title('PySenku')
        main_frame = Frame(self._root, width=280, height=330, bd=1)
        BoardArea(self._game, main_frame)
        start_button = Button(main_frame, text='Nuevo', command=self.start)
        start_button.grid(row=1, column=0, sticky=W)
        UndoButton(self._game, main_frame)
        main_frame.pack()
    
    
    def open_ui(self):
        '''Start the graphic environment.'''
        
        self._game.get_all_changes()
        self._root.mainloop()
    
    
    def start(self):
        '''Reset and start a new game.'''

        self._game.restart()


class BoardArea(Observer):
    '''
    Represent the area in which the player will play.
    
    @ivar _regions: Dictionary <game cell, screen rectangle>
    @ivar _selection: the current cell selected to move.
        If there's no selection, the value is None.
    '''
    
    def __init__(self, game, parent):
        '''Initialize the canvas, the observers and the mouse bindings.'''
        
        self._game = game
        self._game.add_observer(self, 'CELL_OFF')
        self._game.add_observer(self, 'CELL_ON')
        
        self._canvas = Canvas(parent, bg=BOARD_BG_COLOR, width=280, height=280)
        self._canvas.grid(row=0, columnspan=2)
        self._canvas.bind("<Button-1>", self.left_button_pressed)
        
        self._regions = {}
        self.__init_regions(self._game)
        self._selection = None
    
    
    def __init_regions(self, game):
        '''Complete the _regions dictionary.'''
        
        canvas_x = 0
        canvas_y = 0
        for x in range(7):
            for y in range(7):
                if (x, y) in game.get_board():
                    self._regions[(x, y)] =                     \
                        Rectangle((canvas_x, canvas_y),         \
                        (canvas_x + BOARD_RECTANGLE_SIZE - 1,   \
                        canvas_y + BOARD_RECTANGLE_SIZE - 1))
                canvas_x += BOARD_RECTANGLE_SIZE
            canvas_x = 0
            canvas_y += BOARD_RECTANGLE_SIZE
    
    
    def left_button_pressed(self, event):
        '''The mouse left button was pressed, so if there's no
        selection, it's created, and if the selection exists,
        attempt to make a movement taking the selection position
        and the current position.'''
        
        pos = self.get_position_from_pixels(event.x, event.y)
        if pos is not None:
            
            if self._selection is None:
                self._selection = pos
                self.make_selection(pos)
            else:
                self._game.move(self._selection, pos)
                self.clear_selection(self._selection)
                self._selection = None

    
    def make_selection(self, pos):
        '''A selection was made.'''
        
        self.__selection(pos, BOARD_SEL_COLOR)
    
    
    def clear_selection(self, pos):
        '''No longer selection in the position given.'''
        
        self.__selection(pos, BOARD_BG_COLOR)
    
    
    def __selection(self, pos, color):
        '''Draw the selection rectangle.'''
        
        self._regions[pos].display_on(self._canvas, outline=color)
    
    
    def update(self, aspect, value):
        '''The board organization in the model has changed.'''
        
        if aspect == 'CELL_ON':
            self.draw_circle_from_rect(self._regions[value], \
                CELL_NOT_EMPTY_COLOR)
        elif aspect == 'CELL_OFF':
            self.draw_circle_from_rect(self._regions[value], \
                CELL_EMPTY_COLOR)
    
    
    def draw_circle_from_rect(self, rect, color):
        '''Draw a cell empty or not empty.'''
        
        x0 = rect.upper_left()[0] + DIST
        y0 = rect.upper_left()[1] + DIST
        x1 = rect.lower_right()[0] - DIST
        y1 = rect.lower_right()[1] - DIST
        
        self._canvas.create_oval(x0, y0, x1, y1, fill=color)
    
    
    def get_position_from_pixels(self, x, y):
        '''Get the board position corresponding with the
        coordinates given.'''
        
        for k, v in self._regions.items():
            if v.contains((x, y)):
                return k
        return None


class UndoButton(Observer):
    '''Represent the 'undo' button in the Senku GUI.'''
    
    def __init__(self, game, parent):
        '''Constructor of UndoButton. Receive the game and the
        parent widget (frame, in this case).'''
        
        self._game = game
        self._button = Button(parent, text='Deshacer', command=self.undo)
        self._button.grid(row=1, column=1, sticky=E)
        self._game.add_observer(self, 'UNDO_STACK')
    
    
    def update(self, aspect, value):
        '''The aspect is always UNDO_STACK. If there's no undo
        actions, the button will be disabled.'''
        
        if value.is_empty():
            self._button.config(state=DISABLED)
        else:
            self._button.config(state=NORMAL)
    
    
    def undo(self):
        '''Tell the model to perform the undo action, if it's possible.'''

        self._game.undo()


class Rectangle(object):

    def __init__(self, origin, corner):
        '''Constructor of Rectangle.'''
        
        self._origin = origin
        self._corner = corner
    
    
    def __repr__(self):
        '''Printing for Rectangle.'''
        
        return 'Rectangle; origin: ' + repr(self._origin) + \
                ' ; corner: ' + repr(self._corner)
    
    
    def upper_left(self):
        return self._origin

    
    def upper_right(self):
        return (self._origin[0], self._corner[1])
    
    
    def lower_left(self):
        return (self._corner[0], self._origin[1])
    
    
    def lower_right(self):
        return self._corner
    
    
    def contains(self, point):
        '''Receive a tuple (size 2) and check if it's in the rectangle.'''
        
        return point[0] >= self._origin[0] and point[0] <= self._corner[0] \
            and point[1] >= self._origin[1] and point[1] <= self._corner[1]
    
    
    def display_on(self, canvas, **kwargs):
        '''Receive a Tkinter Canvas and draw the rectangle in it.'''
        
        canvas.create_rectangle(self._origin[0], self._origin[1], \
            self._corner[0], self._corner[1], **kwargs)


if __name__ == '__main__':
    
    game = SenkuGame()
    graphic = UISenku(game)
    graphic.open_ui()
