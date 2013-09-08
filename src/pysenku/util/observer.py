'''
Created on 2009.01.14
Last Update on 2009.01.24
@author: Nahuel
'''

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
