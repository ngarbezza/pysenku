'''
    pysenku - A Python implementation of the classic "Senku" game
    Copyright (C) 2010 Nahuel Garbezza
    
    This program is free software; you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation; either version 2 of the License, or
    (at your option) any later version.
    
    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.
    
    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307
    USA

        http://code.google.com/p/pysenku/
'''

__version__ = '0.5'
__date__ = '2010.01.29'
__author__ = 'Nahuel Garbezza'
__copyright__ = "Copyright (C) 2010 Nahuel Garbezza"
__license__ = "GPL"
__email__ = 'n.garbezza@gmail.com'

try:                                    #python3
    from tkinter import Tk, Canvas, Button, Frame, DISABLED, NORMAL, \
        Pack, Toplevel, Checkbutton, E, IntVar, W
    from tkinter.messagebox import askyesno, showinfo
except ImportError:                     #python2
    from Tkinter import Tk, Canvas, Button, Frame, DISABLED, NORMAL, \
        Pack, Toplevel, Checkbutton, E, IntVar, W
    from tkMessageBox import askyesno, showinfo

import pickle

#-----------------------------------------------------------------------------
#---------------------------- CONFIGURATION ----------------------------------
#-------------------------(game default options)------------------------------
HELP_TEXT = """
    PySenku - Version 0.5
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
# UNDO_LEVEL represents the max movements that you can undo. For infinite undo,
# just put a value > 32, because the game doesn't allow more of 32 movements.
CONFIG = {'UNDO_LEVEL' : 5, 'DIAMETER' : 30, 'BOARD_RECT_SIZE' : 40,
          'GAME_TRACKING' : True, 'CONFIRM_EXIT' : True, 
          'BOARD_BG_COLOR' : '#00B000', 'HOLE_COLOR' : 'black',
          'CELL_COLOR' : 'red', 'BOARD_SEL_COLOR' : 'green'}
CONFIG['DIST'] = CONFIG['BOARD_RECT_SIZE'] - CONFIG['DIAMETER']

def read_conf(conf):
    '''Reads the Senku configuration parameters.'''
    try:
        with open('pysenku-config') as conf_file:
            conf = pickle.load(conf_file)
    except IOError:         # first time run or configuration file deleted
        write_conf(conf)    # dump default configuration

def write_conf(conf):
    with open('pysenku-config', 'w') as conf_file:
        pickle.dump(conf, conf_file, pickle.HIGHEST_PROTOCOL)
        conf_file.close()

#-----------------------------------------------------------------------------
#-------------------------- UTILITIES - STACK --------------------------------
#-----------------------------------------------------------------------------

class DynamicBoundedStack(object):
    '''
    Stack with keep a maximum of elements.
    
    @ivar _data: The internal storage (list).
    @ivar _size: maximum of elements.
    '''
    
    def __init__(self, size):
        '''Constructor of DynamicBoundedStack.'''
        self._data = []
        self._size = size
    
    def is_full(self):
        '''Check if the stack is full (reached the max size).'''
        return len(self._data) == self._size
    
    def is_empty(self):
        '''Check if the stack has no elements.'''
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
        for observer in self.observers['all']:  # also notify observers 
            observer.update(aspect, value)      #interested in 'all' aspects
    
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

def avg(a, b):                          #auxiliary function
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
        self._undo_stack = DynamicBoundedStack(CONFIG['UNDO_LEVEL'])
        self._with_tracking = CONFIG['GAME_TRACKING']
    
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
        '''Checks the movement conditions.'''
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
        

class Move(object):
    '''
    A command for Senku moves (allows undo).
    
    @ivar _game: The senku game.
    @ivar _origin: The move's origin position.
    @ivar _dest: The move's destination position.
    @ivar _mid: Position between orig and dest.
    '''
    
    def __init__(self, game, orig, dest):
        '''Constructor of UndoAction.'''
        self._game = game
        self._origin = orig
        self._mid = avg(orig, dest)
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
    
    def get_mid(self):
        '''Getter of _avg.'''
        return self._mid
    
    def execute(self):
        '''Do the movement action.'''
        orig = self.get_origin()
        dest = self.get_dest()
        if self.get_game().check_distance(orig, dest) \
        and self.get_game().check_cells(orig, dest):
            self.get_game().empty_cell(orig)
            self.get_game().fill_cell(dest)
            self.get_game().empty_cell(self.get_mid())
            self.get_game().movement_done(self)
    
    def undo(self):
        '''Perform the undo action, inverted movement.'''
        self.get_game().fill_cell(self.get_origin())
        self.get_game().fill_cell(self.get_mid())
        self.get_game().empty_cell(self.get_dest())

#-----------------------------------------------------------------------------
#---------------------- GRAPHICAL USER INTERFACE -----------------------------
#-----------------------------------------------------------------------------

class UISenku(Observer):
    '''
    Implements the Graphical User Interface to the Senku.
    
    @ivar _game: the game logic (the model).
    @ivar _root: the main window.
    @ivar _conf_opened: indicates if the configuration window
        is opened.
    '''

    def __init__(self, game):
        '''Constructor of UISenku. Build the main window and the
        main frame.'''
        Observer.__init__(self)
        self._game = game           # game parameters
        self._game.add_observer(self, 'GAME_OVER')
        self._root = Tk()           # root window parameters
        self._root.title('PySenku')
        self._root.protocol("WM_DELETE_WINDOW", self.quit)
        main_frame = Frame(self._root, width=280, height=330, bd=1)
        main_frame.pack()
        BoardArea(self._game, main_frame)
        start_button = Button(main_frame)
        start_button.config(text='Nuevo', command=self.start)
        start_button.grid(row=1, column=0)
        help_button = Button(main_frame)
        help_button.config(text='Mas info...', command=self.open_help)
        help_button.grid(row=1, column=2)
        conf_button = Button(main_frame)
        conf_button.config(text='Configuracion...', command=self.open_config)
        conf_button.grid(row=1, column=3)
        UndoButton(self._game, main_frame)
        self._conf_opened = False
    
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
    
    def open_config(self):
        '''Open the configuration window.'''
        if not self._conf_opened:
            self._conf_opened = True
            ConfigWindow().mainloop()
    
    def update(self, aspect, value):
        '''GAME_OVER is the only notification that
        this class receive.'''
        if askyesno('Juego Finalizado', 'Quedaron ' + str(value) + \
            ' fichas.\n \n Comenzar otra partida?'):
            self.start()
    
    def quit(self):
        '''Handler for window close attempt.'''    
        if CONFIG['CONFIRM_EXIT']:
            if askyesno('Salir', 'Realmente desea salir?'): 
                self._root.destroy()
        else:
            self._root.destroy()


class ConfigWindow(Toplevel):
    '''Represent the configuration window.'''
    
    def __init__(self, parent=None):
        '''Constructor of ConfigWindow.'''
        Toplevel.__init__(self, parent)
        self.title('Configuracion')
        self._states = [IntVar(value=CONFIG['GAME_TRACKING']), 
                        IntVar(value=CONFIG['CONFIRM_EXIT'])]
        self._cbox_gtrack = Checkbutton(self, text='Seguimiento del juego')
        self._cbox_gtrack.config(variable=self._states[0])
        self._cbox_confexit = Checkbutton(self, text='Confirmacion al salir')
        self._cbox_confexit.config(variable=self._states[1])
        self._cbox_gtrack.grid(row=0, column=0, sticky=W)
        self._cbox_confexit.grid(row=1, column=0, sticky=W)
        self._button_cancel = Button(self, text='Cancelar', command=self.destroy)
        self._button_cancel.grid(row=3, column=1, sticky=E)
        self._button_accept = Button(self, text='Guardar y Salir')
        self._button_accept.config(command=self.save_config)
        self._button_accept.grid(row=3, column=0, sticky=E)
        
    def save_config(self):
        pass
        
    def get_state_game_tracking(self):
        return self._states[0].get()
    
    def get_state_confirm_exit(self):
        return self._states[1].get()


class BoardArea(Observer):
    '''
    Represent the area in which the player will play.
    
    @ivar _selection: the current cell selected to move.
        If there's no selection, the value is None.
    '''
    
    def __init__(self, game, parent):
        '''Initialize the canvas, the observers and the mouse bindings.'''
        Observer.__init__(self)
        self._game = game
        self._game.add_observer(self, 'CELL_OFF')
        self._game.add_observer(self, 'CELL_ON')
        self._canvas = Canvas(parent, width=280, height=280)
        self._canvas.config(bg=CONFIG['BOARD_BG_COLOR'])
        self._canvas.grid(row=0, columnspan=4)
        self._canvas.bind("<Button-1>", self.left_button_pressed)
        self._selection = None
    
    def get_selection(self):
        '''Getter of _selection.'''
        return self._selection
    
    def set_selection(self, sel):
        '''Setter of _selection.'''
        self._selection = sel
    
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
                move_command = Move(self._game, self.get_selection(), pos)
                move_command.execute()
                self.clear_selection(self.get_selection())
                self.set_selection(None)
    
    def make_selection(self, pos):
        '''A selection was made.'''
        self.draw_sel_rect_from_pos(pos, CONFIG['BOARD_SEL_COLOR'])
    
    def clear_selection(self, pos):
        '''No longer selection in the position given.'''
        self.draw_sel_rect_from_pos(pos, CONFIG['BOARD_BG_COLOR'])
    
    def draw_sel_rect_from_pos(self, pos, color):
        '''Draw the selection rectangle.'''
        rect_size = CONFIG['BOARD_RECT_SIZE']
        origin_x = pos[1] * rect_size
        origin_y = pos[0] * rect_size
        self._canvas.create_rectangle(origin_x, origin_y, \
            origin_x + rect_size, origin_y + rect_size, outline=color)
    
    def update(self, aspect, value):
        '''The board organisation in the model has changed.'''
        if aspect == 'CELL_ON':
            self.draw_circle_from_pos(value, CONFIG['CELL_COLOR'])
        elif aspect == 'CELL_OFF':
            self.draw_circle_from_pos(value, CONFIG['HOLE_COLOR'])
    
    def draw_circle_from_pos(self, pos, color):
        '''Draw a cell empty or not empty.'''
        rect_size = CONFIG['BOARD_RECT_SIZE']
        dist = CONFIG['DIST']
        origin_x = pos[1] * rect_size + dist
        origin_y = pos[0] * rect_size + dist
        corner_x = origin_x + rect_size - dist * 2
        corner_y = origin_y + rect_size - dist * 2
        self._canvas.create_oval(origin_x, origin_y, \
                                 corner_x, corner_y, fill=color)
    
    def get_position_from_pixels(self, x_coord, y_coord):
        '''Get the board position corresponding with the
        coordinates given.'''    
        pos_y = int(x_coord / CONFIG['BOARD_RECT_SIZE'])
        pos_x = int(y_coord / CONFIG['BOARD_RECT_SIZE'])
        if (pos_x, pos_y) in self._game.get_board():
            return (pos_x, pos_y)
        else:
            return None


class UndoButton(Observer):
    '''Represent the 'undo' button in the Senku GUI.'''
    
    def __init__(self, game, parent):
        '''Constructor of UndoButton. Receive the game and the
        parent widget (frame, in this case).'''
        Observer.__init__(self)
        self._game = game
        self._game.add_observer(self, 'UNDO_STACK')
        self._button = Button(parent, text='Deshacer', command=self.undo)
        self._button.grid(row=1, column=1)
    
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

#-----------------------------------------------------------------------------
#--------------------------------- MAIN --------------------------------------
#-----------------------------------------------------------------------------
if __name__ == '__main__':
    read_conf(CONFIG)
    senku = SenkuGame()
    gui_senku = UISenku(senku)
    gui_senku.open_ui()