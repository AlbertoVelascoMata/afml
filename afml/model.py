
import importlib

class Model:
    def __init__(self, source, name=None, params={}):
        self.model_name = name
        self.module_name, self.callable_name = source.split(':')
        self.model_params = params

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

    @property
    def name(self):
        return self.model_name

    @property
    def params(self):
        return self.model_params

    def build(self):
        module = importlib.import_module(self.module_name)
        callable = getattr(module, self.callable_name)
        return callable(**self.model_params)
