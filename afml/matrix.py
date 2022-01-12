
import itertools
from munch import Munch

class Matrix:
    def __init__(self, **entries):
        self._params = entries

    def __iter__(self):
        self._combinations = itertools.product(*self._params.values())
        return self
    
    def __next__(self):
        return MatrixInstance(**dict(zip(self._params.keys(), next(self._combinations))))

class MatrixInstance(Munch):
    def __repr__(self):
        return f"MatrixInstance({', '.join(f'{k}={repr(v)}' for k, v in Munch.toDict(self).items())})"

    def __init__(self, **entries):
        super().__init__(**Munch.fromDict(entries))

    def merge(self, matrix : 'MatrixInstance'):
        return MatrixInstance(**self.__dict__, **matrix.__dict__)
