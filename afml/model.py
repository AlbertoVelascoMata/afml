
import importlib
import importlib.util
from pathlib import Path

from .base import BaseObject
from .utils.format import ParamsFormatter

class Model(BaseObject):
    def __repr__(self):
        return f"Model({', '.join(f'{k}={repr(v)}' for k, v in {'name':super().name, 'source':f'{self.file}:{self.callable}', **self.params}.items())})"

    def __init__(self, source, name : str = None, params : dict = {}):
        super().__init__(name, params)
        self.file, self.callable = source.split(':')

    @property
    def name(self):
        return super().name if super().name else Path(self.file).stem

    def get_formatted(self, formatter : ParamsFormatter):
        return Model(
            name=super().name,
            source=f'{self.file}:{self.callable}',
            params=formatter.format(self.params)
        )

    @staticmethod
    def parse(definition):
        if 'src' not in definition:
            #raise Error
            return None

        return Model(
            source=definition['src'],
            name=definition.get('name'),
            params=definition.get('params') or {}
        )

    def build(self):
        spec = importlib.util.spec_from_file_location(self.name, self.file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        callable = getattr(module, self.callable)

        return callable(**self._params)
