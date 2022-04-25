
import pickle
from argparse import ArgumentParser

from afml.utils.format import ParamsFormatter
from .dataset import Dataset
from .model import Model
    

class RunContext:
    def __init__(self, project, job, step, dataset=None, model=None, formatter=ParamsFormatter()):
        self.project_params = formatter.format(project.params)
        self.job_params = formatter.format(job.params)
        self.step_params = formatter.format(step.params)
        self.dataset : 'Dataset' = dataset
        self.model : 'Model' = model.get_formatted(formatter) if model else None

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

    @staticmethod
    def get_current() -> 'RunContext':
        parser = ArgumentParser()
        parser.add_argument('--afml-context', dest='afml_context_file')
        args, _ = parser.parse_known_args()

        if not args.afml_context_file:
            return None

        return RunContext.load(args.afml_context_file)


run_ctx = RunContext.get_current()
