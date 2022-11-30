
from string import Formatter
from munch import Munch

from .time import Time

class ParamsFormatter:
    @staticmethod
    def format_param(__param__, **key_dict):
        if not isinstance(__param__, str):
            if isinstance(__param__, list):
                return [ParamsFormatter.format_param(item, **key_dict) for item in __param__]
            if isinstance(__param__, dict):
                return ParamsFormatter.format_params(__param__, **key_dict)
            return __param__

        try:
            # Detect single variable parameter expressions, such as '{variable}'
            # This is useful if the variable is a number/list/dict, because it avoids returning it as a string
            # i.e.:
            #   params:
            #     number: 64
            #     input_size: '{number}'
            # Now params.input_size == 5, instead of params.input_size == '5'
            formatable_vars = list(Formatter().parse(__param__))
            if len(formatable_vars) == 1 and formatable_vars[0][0] == '' and formatable_vars[0][1] is not None and formatable_vars[0][2] == '':
                return eval(formatable_vars[0][1], {**Time.get_params(), **key_dict})

            # Otherwise, format as usual
            return __param__.format(**{**Time.get_params(), **key_dict})

        except ValueError as e:
            raise ValueError(f"An error ocurred when trying to format '{__param__}': {e.args[0]}")
        except KeyError as e:
            raise KeyError(f"'{e.args[0]}' not found when formatting '{__param__}'")
        except AttributeError as e:
            raise AttributeError(f"{e.args[0]}, parsing '{__param__}'")

    @staticmethod
    def format_params(__params__, **key_dict):
        if not __params__ or len(__params__) == 0:
            return {}

        formatted_params = Munch()
        for key in __params__:
            formatted_params[key] = ParamsFormatter.format_param(__params__[key], **{**key_dict, **formatted_params})

        return formatted_params

    def __init__(self, **params):
        self._params = params

    def update(self, params):
        '''Format the new parameters and add them to the formatting dictionary'''
        self._params.update(**ParamsFormatter.format_params(params, **self._params))

    def format(self, params : 'str | dict'):
        '''Format a string with the current context definition'''
        if isinstance(params, str):
            return ParamsFormatter.format_param(params, **self._params)
        if isinstance(params, dict):
            return ParamsFormatter.format_params(params, **self._params)
        return params

    def copy(self):
        return ParamsFormatter(**self._params)
