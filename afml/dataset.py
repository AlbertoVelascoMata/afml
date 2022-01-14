from .base import BaseObject

from pathlib import Path

class Dataset(BaseObject):
    def __repr__(self):
        return f"Dataset({', '.join(f'{k}={repr(v)}' for k, v in {'name':super().name, 'folder':self._folder, **self.params}.items())})"

    def __init__(self, folder, name : str = None, params={}):
        super().__init__(name, params)
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
            folder=definition['folder'],
            params=definition.get('params', {})
        )
