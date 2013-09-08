'''
Created on 2009.01.14
Last Update on 2009.01.24
@author: Nahuel
'''

try:                                    #python3
    from tkinter import Tk, Canvas, Button, Frame, DISABLED, NORMAL
    from tkinter.messagebox import askyesno, showinfo
except ImportError:                     #python2
    from Tkinter import Tk, Canvas, Button, Frame, DISABLED, NORMAL
    from tkMessageBox import askyesno, showinfo

from pysenku.util.observer import Observer
from pysenku.model.move import Move

VERSION = 0.2
BOARD_RECTANGLE_SIZE = 40
DIAMETER = 30 
DIST = BOARD_RECTANGLE_SIZE - DIAMETER

# board background color
BOARD_BG_COLOR = '#00B000'      #dark green
# selection color
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
        UndoButton(self._game, main_frame)
                    
    
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
        
        self.draw_sel_rect_from_pos(pos, BOARD_SEL_COLOR)
    
    
    def clear_selection(self, pos):
        '''No longer selection in the position given.'''
        
        self.draw_sel_rect_from_pos(pos, BOARD_BG_COLOR)
    
        
    def draw_sel_rect_from_pos(self, pos, color):
        '''Draw the selection rectangle.'''
        
        origin_x = pos[1] * BOARD_RECTANGLE_SIZE
        origin_y = pos[0] * BOARD_RECTANGLE_SIZE
        corner_x = origin_x + BOARD_RECTANGLE_SIZE
        corner_y = origin_y + BOARD_RECTANGLE_SIZE
        
        self._canvas.create_rectangle(origin_x, origin_y, \
                                      corner_x, corner_y, outline=color)
    
    
    def update(self, aspect, value):
        '''The board organisation in the model has changed.'''
        
        if aspect == 'CELL_ON':
            self.draw_circle_from_pos(value, CELL_NOT_EMPTY_COLOR)
        elif aspect == 'CELL_OFF':
            self.draw_circle_from_pos(value, CELL_EMPTY_COLOR)
    
    
    def draw_circle_from_pos(self, pos, color):
        '''Draw a cell empty or not empty.'''
        
        origin_x = pos[1] * BOARD_RECTANGLE_SIZE + DIST
        origin_y = pos[0] * BOARD_RECTANGLE_SIZE + DIST
        corner_x = origin_x + BOARD_RECTANGLE_SIZE - DIST * 2
        corner_y = origin_y + BOARD_RECTANGLE_SIZE - DIST * 2
    
        self._canvas.create_oval(origin_x, origin_y, \
                                 corner_x, corner_y, fill=color)
    
    
    def get_position_from_pixels(self, x_coord, y_coord):
        '''Get the board position corresponding with the
        coordinates given.'''
        
        pos_y = int(x_coord / BOARD_RECTANGLE_SIZE)
        pos_x = int(y_coord / BOARD_RECTANGLE_SIZE)
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