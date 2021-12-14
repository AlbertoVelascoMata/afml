from datetime import datetime
from string import Formatter

RUN_TIME = datetime.now()

class Utils:
    @staticmethod
    def format_param(param, **key_dict):
        if not isinstance(param, str):
            return param

        try:
            # Detect single variable parameter expressions, such as '{variable}'
            # This is useful if the variable is a number/list/dict, because it avoids returning it as a string
            # i.e.:
            #   params:
            #     number: 64
            #     input_size: '{number}'
            # Now params.input_size == 5, instead of params.input_size == '5'
            formatable_vars =  [var for pre, var, format, _ in Formatter().parse(param) if var is not None and pre == '' and format == '']
            if len(formatable_vars) == 1:
                return eval(formatable_vars[0], {**key_dict, 'time': RUN_TIME.strftime("%d-%m-%Y-%H-%M-%S")})
            
            # Otherwise, format as usual
            else:
                return param.format(**key_dict, time=RUN_TIME.strftime("%d-%m-%Y-%H-%M-%S"))
    
        except KeyError as e:
            raise KeyError(f"'{e.args[0]}' not found when formatting '{param}'")
        except AttributeError as e:
            raise AttributeError(f"{e.args[0]}, parsing '{param}'")

    @staticmethod
    def format_params(params, **key_dict):
        if not params or len(params) == 0: return {}
        params = params.copy()
        for key in params:
            params[key] = Utils.format_param(params[key], **{**key_dict, **params})

        return params


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
