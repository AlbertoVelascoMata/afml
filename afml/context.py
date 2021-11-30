
from pathlib import Path
import pickle
from argparse import ArgumentParser
from datetime import datetime

from .dataset import Dataset
from .model import Model

RUN_TIME = datetime.now()

def format_params(params, **key_dict):
    if not params or len(params) == 0: return {}
    params = params.copy()
    for key in params:
        if isinstance(params[key], str):
            params[key] = params[key].format(**key_dict, **params,
                                             time=RUN_TIME.strftime("%d_%m_%Y_%H_%M_%S"))

    return params

class RunContext:
    def __init__(self, project, job, step, dataset=None, model=None):
        self.project_params = format_params(project.params)
        self.job_params = format_params(job.params,
                                        **self.project_params,
                                        job=job.display_name,
                                        dataset=dataset.name if dataset else 'undefined',
                                        model=model.name if model else 'undefined')
        self.step_params = format_params(step.params,
                                         **self.project_params,
                                         job=job.display_name,
                                         dataset=dataset.name if dataset else 'undefined',
                                         model=model.name if model else 'undefined',
                                         **self.job_params,
                                         step=step.display_name)
        self.dataset : 'Dataset' = dataset
        self.model : 'Model' = model

    @property
    def params(self) -> 'dict':
        return {
            **self.project_params,
            **self.job_params,
            **self.step_params
        }

    def dump(self, file):
        with open(file, 'wb') as f:
            pickle.dump(self, f)

    @staticmethod
    def load(file) -> 'RunContext':
        with open(file, 'rb') as f:
            return pickle.load(f)
            #params = pickle.load(f)
        #return RunContext()

    @staticmethod
    def get_current() -> 'RunContext':
        parser = ArgumentParser()
        parser.add_argument('--afml-context', dest='afml_context_file')
        args, _ = parser.parse_known_args()

        if not args.afml_context_file:
            return None

        return RunContext.load(args.afml_context_file)


run_ctx = RunContext.get_current()
