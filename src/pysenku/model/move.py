'''
Created on 2009.01.25
Last Update on 2009.01.25
@author: Nahuel
'''

import pysenku.model.senkugame

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
        self._mid = pysenku.model.senkugame.avg(orig, dest)
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