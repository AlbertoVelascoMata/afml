import os
from termcolor import cprint

from .format import ParamsFormatter

class Utils:
    @staticmethod
    def check_condition(condition, expression):
        if condition == 'file':
            return os.path.isfile(expression)

        elif condition == 'not_file':
            return not os.path.isfile(expression)
        else:
            cprint(f"WARNING: '{condition}' is not a valid condition", 'yellow')
            return True
    
    @staticmethod
    def check_conditions(conditions, formatter=ParamsFormatter()):
        return all(Utils.check_condition(condition, formatter.format(expression))
                   for condition, expression in conditions.items())
