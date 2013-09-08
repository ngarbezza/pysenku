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
__author__ = 'Nahuel Garbezza'
__copyright__ = "Copyright (C) 2010 Nahuel Garbezza"
__license__ = "GPL"
__email__ = 'n.garbezza@gmail.com'


from pysenku.model.senkugame    import SenkuGame
from pysenku.ui.uisenku         import UISenku

if __name__ == '__main__':
    
    senku = SenkuGame()
    gui_senku = UISenku(senku)
    gui_senku.open_ui()
