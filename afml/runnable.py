from typing import Union

from .base import BaseObject
from .dataset import Dataset
from .model import Model
from .utils.format import ParamsFormatter
from .utils.utils import Utils

class RunnableObject(BaseObject):
    def __init__(self, name : str = None, params : dict = {}, dataset : Union[Dataset, str, None] = None, model : Union[Model, str, None] = None, conditions : dict = {}):
        super().__init__(name, params)
        self._dataset = dataset
        self._model = model
        self._conditions = conditions or {}

    def get_dataset(self, project, formatter=ParamsFormatter()):
        dataset_definition = formatter.format(self._dataset)
        if isinstance(dataset_definition, str):
            return project.get_dataset(dataset_definition)
        elif isinstance(dataset_definition, dict):
            return Dataset.parse(dataset_definition)
        else:
            return None
    
    def get_model(self, project, formatter=ParamsFormatter()):
        model_definition = formatter.format(self._model)
        if isinstance(model_definition, str):
            return project.get_model(model_definition)
        elif isinstance(model_definition, dict):
            return Model.parse(model_definition)
        else:
            return None
    
    def can_execute(self, formatter=ParamsFormatter()):
        return Utils.check_conditions(self._conditions, formatter)
