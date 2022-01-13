import os
import json
from datetime import datetime
from string import Formatter

from munch import Munch

class Time:
    _instance = None

    def __init__(self):
        self.last_time = self.run_time = datetime.now()

        run_data_file = '.afml/run_data.json'
        if os.path.isfile(run_data_file):
            with open(run_data_file, 'r') as f:
                run_data = json.load(f)
            
            if 'last_time' in run_data:
                self.last_time = datetime.fromisoformat(run_data['last_time'])
        
        with open(run_data_file, 'w') as f:
            json.dump({
                'last_time': self.run_time.isoformat()
            }, f)

    @property
    def params(self):
        return {
            'time': self.run_time.strftime("%d-%m-%Y-%H-%M-%S"),
            'last_time': self.last_time.strftime("%d-%m-%Y-%H-%M-%S")
        }

    @staticmethod
    def get_params():
        t = Time.get_instance()
        return t.params

    @staticmethod
    def get_instance():
        if Time._instance is None:
            Time._instance = Time()
        
        return Time._instance

class Utils:
    @staticmethod
    def format_param(param, **key_dict):
        if not isinstance(param, str):
            if isinstance(param, list):
                return [Utils.format_param(item, **key_dict) for item in param]
            elif isinstance(param, dict):
                return Utils.format_params(param, **key_dict)
            else:
                return param

        try:
            # Detect single variable parameter expressions, such as '{variable}'
            # This is useful if the variable is a number/list/dict, because it avoids returning it as a string
            # i.e.:
            #   params:
            #     number: 64
            #     input_size: '{number}'
            # Now params.input_size == 5, instead of params.input_size == '5'
            formatable_vars = list(Formatter().parse(param))
            if len(formatable_vars) == 1 and formatable_vars[0][0] == '' and formatable_vars[0][1] is not None and formatable_vars[0][2] == '':
                return eval(formatable_vars[0][1], {**key_dict, **Time.get_params()})
            
            # Otherwise, format as usual
            else:
                return param.format(**key_dict, **Time.get_params())
    
        except KeyError as e:
            raise KeyError(f"'{e.args[0]}' not found when formatting '{param}'")
        except AttributeError as e:
            raise AttributeError(f"{e.args[0]}, parsing '{param}'")

    @staticmethod
    def format_params(params, **key_dict):
        if not params or len(params) == 0: return {}
        formatted_params = Munch()
        for key in params:
            formatted_params[key] = Utils.format_param(params[key], **{**key_dict, **formatted_params})

        return formatted_params


class ParamsFormatter:
    def __init__(self, **params):
        self._params = params
        
    def update(self, params):
        '''Format the new parameters and add them to the formatting dictionary'''
        self._params.update(**Utils.format_params(params, **self._params))

    def format(self, params : 'str | dict'):
        '''Format a string with the current context definition'''
        if isinstance(params, str):
            return Utils.format_param(params, **self._params)
        elif isinstance(params, dict):
            return Utils.format_params(params, **self._params)
        else:
            return params
    
    def copy(self):
        return ParamsFormatter(**self._params)
