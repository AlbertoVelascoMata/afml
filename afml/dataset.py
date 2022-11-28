from pathlib import Path

from .base import BaseObject

class Dataset(BaseObject):
    def __repr__(self):
        args = ', '.join(
            f'{k}={repr(v)}'
            for k, v in {
                'name': super().name,
                'folder': self._folder,
                **self.params
            }.items()
        )
        return f"Dataset({args})"

    def __init__(self, folder, name: str = None, params: dict = None):
        super().__init__(name, params)
        self._folder = folder

    @property
    def name(self) -> str:
        return super().name if super().name else self.folder.stem

    @property
    def folder(self) -> Path:
        return Path(self._folder)

    @staticmethod
    def parse(definition: dict):
        if 'folder' not in definition:
            #raise Error
            return None

        return Dataset(
            folder=definition['folder'],
            name=definition.get('name'),
            params=definition.get('params', None)
        )
