from .base import BaseObject

from pathlib import Path

class Dataset(BaseObject):
    def __init__(self, folder, name : str = None):
        super().__init__(name)
        self._folder = folder

    @property
    def name(self) -> 'str':
        return super().name if super().name else self.folder.stem
    
    @property
    def folder(self) -> 'Path':
        return Path(self._folder)
    
    @staticmethod
    def parse(definition):
        if 'folder' not in definition:
            #raise Error
            return None
        
        return Dataset(
            name=definition.get('name', None),
            folder=definition['folder']
        )
