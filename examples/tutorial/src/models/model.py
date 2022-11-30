
class ModelImplementation:
    def __init__(self, input_size):
        self.input_size = input_size
    
    def summary(self):
        print(f'== Example Model ==\n  input_size: {self.input_size}\n===================')

def build(input_size, **params):
    return ModelImplementation(input_size)

def model_method():
    return 42
