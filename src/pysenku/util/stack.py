'''
Created on 2009.01.14
Last Update on 2009.01.24
@author: Nahuel
'''

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