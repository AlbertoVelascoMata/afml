
import pickle
from argparse import ArgumentParser
from pathlib import Path

from munch import Munch, munchify

from .utils.format import ParamsFormatter
from .dataset import Dataset
from .model import Model


class RunContext:
    def __init__(self, project, job, step, dataset=None, model=None, formatter=ParamsFormatter()):
        self._params = None
        self.project_params = formatter.format(project.params)
        self.job_params = formatter.format(job.params)
        self.step_params = formatter.format(step.params)
        self.dataset : 'Dataset' = dataset
        self.model : 'Model' = model.get_formatted(formatter) if model else None

    @property
    def params(self) -> 'Munch':
        if self._params is None:
            self._params = munchify({
                **self.project_params,
                **self.job_params,
                **self.step_params
            })
        return self._params

    def dump(self, file):
        with open(file, 'wb') as serialized_file:
            pickle.dump(self, serialized_file)

    @staticmethod
    def load(file) -> 'RunContext':
        with open(file, 'rb') as serialized_file:
            return pickle.load(serialized_file)

    @staticmethod
    def get_current() -> 'RunContext':
        parser = ArgumentParser(add_help=False)
        parser.add_argument('--afml-context', type=Path, dest='afml_context_file')
        try:
            args, _ = parser.parse_known_args()
        except SystemExit:
            return None

        if not args.afml_context_file or not args.afml_context_file.is_file():
            return None

        return RunContext.load(args.afml_context_file)


run_ctx = RunContext.get_current()
