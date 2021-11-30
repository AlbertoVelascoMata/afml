
import importlib
import importlib.util

from .base import BaseObject

class Model(BaseObject):
    def __init__(self, source, name=None, params={}):
        super().__init__(name, params)
        self.file, self.callable = source.split(':')

    @property
    def name(self):
        return super().name if super().name else self.file

    @staticmethod
    def parse(definition):
        if 'src' not in definition:
            #raise Error
            return None

        return Model(
            name=definition.get('name', None),
            source=definition['src'],
            params=definition.get('params', {})
        )

    def build(self):
        spec = importlib.util.spec_from_file_location(self.name, self.file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)

        callable = getattr(module, self.callable)

        return callable(**self._params)
