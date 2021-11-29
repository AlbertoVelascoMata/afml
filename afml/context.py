
from pathlib import Path
import pickle

class RunContext:
    def __init__(self):
        with open('.afml/step_params.pickle', 'rb') as f:
            self.params = pickle.load(f)

