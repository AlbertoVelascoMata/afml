
class BaseObject:
    def __init__(self, name=None, params={}):
        self._name = name
        self._params = params if params else {}

    @property
    def name(self):
        return self._name

    @property
    def params(self):
        return self._params
