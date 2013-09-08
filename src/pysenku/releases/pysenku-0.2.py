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

__version__ = '0.2'
__author__ = 'Nahuel Garbezza'
__copyright__ = "Copyright (C) 2010 Nahuel Garbezza"
__license__ = 'gpl'
__email__ = 'n.garbezza@gmail.com'

try:                                    #python3
    from tkinter import Tk, Canvas, Button, Frame, DISABLED, NORMAL
    from tkinter.messagebox import askyesno, showinfo
except ImportError:                     #python2
    from Tkinter import Tk, Canvas, Button, Frame, DISABLED, NORMAL
    from tkMessageBox import askyesno, showinfo

#-----------------------------------------------------------------------------
#-------------------------- UTILITIES - STACK --------------------------------
#-----------------------------------------------------------------------------

class DynamicBoundedStack(object):
    '''
    Stack with keep a maximum of elements.
    
    @ivar _data: The internal storage (list).
    @ivar _size: maximum of elements
    '''
    
    def __init__(self, size):
        '''Constructor of DynamicBoundedStack.'''
        
        self._data = []
        self._size = size
    
    
    def is_full(self):
        '''Check if the stack is full (reached the max size).'''
        
        return len(self._data) == self._size
    
    
    def is_empty(self):
        '''Ckeck if the stack has no elements.'''
        
        return not self._data
    
    
    def make_empty(self):
        '''Remove all elements in the stack.'''
        
        self._data = []
    
    
    def push(self, elem):
        '''Always put the element, but if the stack reach
        the limit, removes the oldest element.'''
        
        if self.is_full():
            self._data.pop(0)       # the first element pushed (oldest)
        
        self._data.append(elem)
    
    
    def pop(self):
        '''Removes the last element pushed.'''
        
        return self._data.pop()

#-----------------------------------------------------------------------------
#-------------------------- UTILITIES - OBSERVER -----------------------------
#-----------------------------------------------------------------------------

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
        
        try:
            for observer in self.observers[aspect]:
                observer.update(aspect, value)
        except KeyError:
            self.add_aspect(aspect)
            for observer in self.observers[aspect]:
                observer.update(aspect, value)
        # also notify observers interested in 'all' aspects
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

#-----------------------------------------------------------------------------
#------------------------------- GAME LOGIC ----------------------------------
#-----------------------------------------------------------------------------

# Max movements that you can undo. For infinite undo, just put a value > 32, 
# because the game doesn't allow more of 32 movements.
MAX_UNDO_ACTIONS = 5

# Game tracking (control the game end). True to enable, False to disable
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
    @ivar _with_tracking: Game tracking (control the game end)
    
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
    
    
    def move(self, orig, dest):
        '''Receive two tuples and make the movement from origin to 
        destination, if it's possible. Also add a UndoAction to the stack.
        If tracking is enabled, checks when the game is over.'''
        
        if self.__check_dist(orig, dest) and self.__check_cells(orig, dest):
            self.fill_cell(dest)
            self.empty_cell(orig)
            self.empty_cell(avg(orig, dest))
            self.get_undo_stack().push(UndoAction(self, orig, dest))
            self.notify('UNDO_STACK', self.get_undo_stack())
            if self._with_tracking:
                self.check_end()
    
    
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
        
        return self._board[orig] and not self._board[dest] \
            and self._board[avg(orig, dest)]
    
    
    def undo(self):
        '''Undo the last action, if it's possible.'''
        
        self.get_undo_stack().pop().undo()
        self.notify('UNDO_STACK', self._undo_stack)
    
    
    def check_end(self):
        '''Check if there's no possible movements, then notify
        if the game is over.'''
        
        cells_left = 0
        for pos1, cell in self.get_board().items():
            if cell:
                for pos2 in self.get_board():
                    if self.__check_dist(pos1, pos2) \
                    and self.__check_cells(pos1, pos2):
                        return None         # movement
                cells_left += 1
        self.notify('GAME_OVER', cells_left)
    
    
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
        '''Getter of _game.'''
        
        return self._game
    
    
    def get_origin(self):
        '''Getter of _origin.'''
        
        return self._origin
    
    
    def get_dest(self):
        '''Getter of _dest.'''
        
        return self._dest
    
    
    def undo(self):
        '''Perform the undo action, inverted movement.'''
        
        self.get_game().fill_cell(self.get_origin())
        self.get_game().fill_cell(avg(self.get_origin(), self.get_dest()))
        self.get_game().empty_cell(self.get_dest())

#-----------------------------------------------------------------------------
#---------------------- GRAPHICAL USER INTERFACE -----------------------------
#-----------------------------------------------------------------------------

BOARD_RECTANGLE_SIZE = 40
CELL_DIAMETER = 30 
DIST = BOARD_RECTANGLE_SIZE - CELL_DIAMETER
BOARD_BG_COLOR = '#00B000'      #dark green
BOARD_SEL_COLOR = 'green'

CELL_EMPTY_COLOR = 'black'
CELL_NOT_EMPTY_COLOR = 'red'

CONFIRM_EXIT = True

HELP_TEXT = """
    PySenku - Version 0.2
    por Nahuel Garbezza (n.garbezza@gmail.com)

    Reglamento y caracteristicas del juego:
    
    *. Las 32 fichas inicialmente estan dispuestas de forma
        que el centro quede libre.
    *. Cada movimiento debe ser en direccion horizontal o
        vertical, saltando sobre una ficha hacia un lugar libre.
    *. No son posibles saltos diagonales o movimientos sin
        saltar sobre una ficha.
    *. El objetivo es eliminar la mayor cantidad de fichas 
        posibles, y el resultado perfecto es quedarse con una
        ficha, y que esta quede en el centro del tablero.
"""

class UISenku(Observer):
    '''
    Implements the Graphical User Interface to the Senku.
    
    @ivar _game: the game logic (the model).
    @ivar _root: the main window.
    '''
    
    def __init__(self, game):
        '''Constructor of UISenku. Build the main window and the
        main frame.'''
        
        Observer.__init__(self)
        self._game = game
        self._root = Tk()
        self._root.title('PySenku')
        main_frame = Frame(self._root, width=280, height=330, bd=1)
        BoardArea(self._game, main_frame)
        start_button = Button(main_frame)
        start_button.config(text='Nuevo', command=self.start)
        start_button.grid(row=1, column=0)
        help_button = Button(main_frame)
        help_button.config(text='Mas info...', command=self.open_help)
        help_button.grid(row=1, column=2)
        UndoButton(self._game, main_frame)
        main_frame.pack()
        self._game.add_observer(self, 'GAME_OVER')
        self._root.protocol("WM_DELETE_WINDOW", self.quit)
    
    
    def open_ui(self):
        '''Start the graphic environment.'''
        
        self._game.get_all_changes()
        self._root.mainloop()
    
    
    def start(self):
        '''Reset and start a new game.'''
        
        self._game.restart()
    
    
    def open_help(self):
        '''Open the help window.'''
        
        showinfo('Mas info...', HELP_TEXT)
    
    
    def update(self, aspect, value):
        '''GAME_OVER is the only notification that
        this class receive.'''
        
        if askyesno('Juego Finalizado', 'Quedaron ' + str(value) + \
            ' fichas.\n \n Comenzar otra partida?'):
            self.start()
    
    
    def quit(self):
        '''Handler for window close attempt.'''
        
        if askyesno('Salir', 'Realmente desea salir?') or not CONFIRM_EXIT:
            self._root.destroy()


class BoardArea(Observer):
    '''
    Represent the area in which the player will play.
    
    @ivar _regions: Dictionary <game cell, screen rectangle>
    @ivar _selection: the current cell selected to move.
        If there's no selection, the value is None.
    '''
    
    def __init__(self, game, parent):
        '''Initialize the canvas, the observers and the mouse bindings.'''
        
        Observer.__init__(self)
        self._game = game
        self._game.add_observer(self, 'CELL_OFF')
        self._game.add_observer(self, 'CELL_ON')
        
        self._canvas = Canvas(parent, bg=BOARD_BG_COLOR, width=280, height=280)
        self._canvas.grid(row=0, columnspan=3)
        self._canvas.bind("<Button-1>", self.left_button_pressed)
        
        self._regions = {}
        self.__init_regions(self._game)
        self._selection = None
    
    
    def get_selection(self):
        '''Getter of _selection.'''
        
        return self._selection
    
    
    def set_selection(self, sel):
        '''Setter of _selection.'''
        
        self._selection = sel
    
    
    def __init_regions(self, game):
        '''Complete the _regions dictionary.'''
        
        canvas_x = 0
        canvas_y = 0
        for x_index in range(7):
            for y_index in range(7):
                if (x_index, y_index) in game.get_board():
                    self._regions[(x_index, y_index)] =         \
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
            if self.get_selection() is None:
                self.set_selection(pos)
                self.make_selection(pos)
            else:
                self._game.move(self.get_selection(), pos)
                self.clear_selection(self.get_selection())
                self.set_selection(None)
    
    
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
        
        origin_x = rect.upper_left()[0] + DIST
        origin_y = rect.upper_left()[1] + DIST
        corner_x = rect.lower_right()[0] - DIST
        corner_y = rect.lower_right()[1] - DIST
        
        self._canvas.create_oval(origin_x, origin_y, \
                                 corner_x, corner_y, fill=color)
    
    
    def get_position_from_pixels(self, x_coord, y_coord):
        '''Get the board position corresponding with the
        coordinates given.'''
        
        for cell, rect in self._regions.items():
            if rect.contains((x_coord, y_coord)):
                return cell
        return None


class UndoButton(Observer):
    '''Represent the 'undo' button in the Senku GUI.'''
    
    def __init__(self, game, parent):
        '''Constructor of UndoButton. Receive the game and the
        parent widget (frame, in this case).'''
        
        Observer.__init__(self)
        self._game = game
        self._button = Button(parent, text='Deshacer', command=self.undo)
        self._button.grid(row=1, column=1)
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
    '''Represent a Rectangle region.'''
    
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
        '''Receive a Tkinter Canvas and draw the rectangle on it.'''
        
        canvas.create_rectangle(self._origin[0], self._origin[1], \
            self._corner[0], self._corner[1], **kwargs)

#-----------------------------------------------------------------------------
#--------------------------------- MAIN --------------------------------------
#-----------------------------------------------------------------------------

if __name__ == '__main__':
    game = SenkuGame()
    graphic = UISenku(game)
    graphic.open_ui()