
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
        self._module = None

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
    
    @property
    def module(self):
        if not self._module:
            spec = importlib.util.spec_from_file_location(self.name, self.file)
            self._module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(self._module)
        return self._module

    def build(self, **kwargs):
        callable = getattr(self.module, self.callable)

        params = {**self._params, **kwargs}
        return callable(**params)
