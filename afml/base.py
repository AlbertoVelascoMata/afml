from munch import munchify

class BaseObject:
    def __init__(self, name: str = None, params: dict = None):
        self._name = name
        self._params = munchify(params or {})

    @property
    def name(self) -> str:
        return self._name

    @property
    def params(self) -> dict:
        return self._params
