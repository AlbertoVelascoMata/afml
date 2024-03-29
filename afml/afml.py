"""
    Automation Framework for Machine Learning
"""
import os
import pickle
from argparse import ArgumentParser
from typing import List

import yaml
from termcolor import cprint

from .base import BaseObject
from .context import RunContext
from .dataset import Dataset
from .executor import Executor, get_executor
from .matrix import Matrix, MatrixInstance
from .model import Model
from .runnable import RunnableObject
from .utils.format import ParamsFormatter


class DatasetNotFoundError(LookupError): ...
class ModelNotFoundError(LookupError): ...
class JobNotFoundError(LookupError): ...

class Step(RunnableObject):
    index = 0

    def __repr__(self):
        args = ', '.join(
            f'{k}={repr(v)}'
            for k, v in {
                'name': self.display_name,
                'executor': self.executor,
                **self.params
            }.items()
        )
        return f"Step({args})"

    def __init__(
        self,
        executor: Executor,
        name: str = None,
        params: dict = None,
        dataset: Dataset = None,
        model: Model = None,
        conditions: dict = None
    ):
        super().__init__(name, params, dataset, model, conditions)
        self.index = Step.index
        Step.index += 1
        self.executor = executor

    @property
    def display_name(self):
        return self.name if self.name else f"Step {self.index+1}"

    @staticmethod
    def parse(definition):
        return Step(
            executor=get_executor(definition),
            name=definition.get('name'),
            params=definition.get('params') or {},
            dataset=definition.get('dataset'),
            model=definition.get('model'),
            conditions=definition.get('if') or {}
        )

    def run(
        self,
        project: 'Project',
        job: 'Job',
        dataset: Dataset = None,
        model: Model = None,
        formatter=ParamsFormatter()
    ):
        cprint(f"---- {self.display_name} [{self.executor}] ----", 'blue')

        formatter.update({'step': self})

        step_dataset = self.get_dataset(project, formatter)
        if step_dataset is not None:
            dataset = step_dataset

        step_model = self.get_model(project, formatter)
        if step_model is not None:
            model = step_model

        formatter.update({
            'dataset': dataset,
            'model': model
        })
        formatter.update(self.params)

        if not self.can_execute(formatter):
            cprint("Skipping step", 'yellow')
            return False

        ctx = RunContext(project, job, self, dataset, model, formatter)
        process = self.executor.start(ctx, formatter)
        for stderr in process:
            cprint(stderr, 'yellow', end='')
        if process.exit_code != 0:
            cprint("ERROR: Step execution failed!", 'red')

class Job(RunnableObject):
    index = 0

    def __repr__(self):
        args = ', '.join(
            f'{k}={repr(v)}'
            for k, v in {
                'name': self.display_name,
                **self.params
            }.items()
        )
        return f"Job({args})"

    def __init__(
        self,
        steps: List[Step],
        name: str = None,
        params: dict = None,
        dataset: Dataset = None,
        model: Model = None,
        conditions: dict = None,
        matrix: Matrix = None
    ):
        super().__init__(name, params, dataset, model, conditions)
        self.index = Job.index
        Job.index += 1
        self.steps = steps
        self.matrix = matrix or Matrix()

    @property
    def display_name(self):
        return self.name if self.name else f"Job {self.index+1}"

    @staticmethod
    def parse(definition):
        if 'steps' not in definition:
            #raise Error
            return None

        return Job(
            steps=[Step.parse(step) for step in definition['steps']],
            name=definition.get('name'),
            params=definition.get('params') or {},
            dataset=definition.get('dataset'),
            model=definition.get('model'),
            conditions=definition.get('if') or {},
            matrix = Matrix(**(definition.get('matrix') or {})),
        )

    def get_step(self, step_name):
        pass

    def run(self, project, project_matrix=MatrixInstance()):
        cprint(f"==== {self.display_name} ====", 'green')

        for job_matrix in self.matrix:
            if len(job_matrix) > 0:
                cprint(f" {str(job_matrix):-<100}", 'magenta', 'on_white')
            matrix = project_matrix.merge(job_matrix)

            formatter = ParamsFormatter(matrix=matrix)
            formatter.update(project.params)
            formatter.update({'job': self})

            dataset = self.get_dataset(project, formatter)
            model = self.get_model(project, formatter)

            formatter.update({
                'dataset': dataset,
                'model': model
            })
            formatter.update(self.params)

            if not self.can_execute(formatter):
                cprint("Skipping job", 'yellow')
                return False

            for step in self.steps:
                failed = step.run(
                    project, self, dataset, model, formatter.copy()
                )
                if failed:
                    return True
                print()

        return False

class Project(BaseObject):
    def __repr__(self):
        return f"Project({', '.join(f'{k}={repr(v)}' for k, v in self.params.items())})"

    def __init__(
        self,
        datasets: List[Dataset] = None,
        models: List[Model] = None,
        jobs: List[Job] = None,
        matrix: Matrix = None,
        params: dict = None
    ):
        super().__init__(params=params)
        self.datasets: List[Dataset] = datasets or []
        self.models: List[Model] = models or []
        self.jobs: List[Job] = jobs or []
        self.matrix: Matrix = matrix or Matrix()

    @staticmethod
    def load(file):
        with open(file, 'r', encoding='utf-8') as project_file:
            definition = yaml.safe_load(project_file)

        return Project(
            datasets=[
                Dataset.parse(dataset)
                for dataset in definition.get('datasets', [])
            ],
            models=[
                Model.parse(model)
                for model in definition.get('models', [])
            ],
            jobs=[
                Job.parse(job)
                for job in definition.get('jobs', [])
            ],
            matrix=Matrix(**definition.get('matrix', {})),
            params=definition.get('params', {}),
        )

    def get_dataset(self, dataset_name):
        if not dataset_name:
            raise ValueError("No dataset name provided")

        for dataset in self.datasets:
            if dataset_name == dataset.name:
                return dataset

        raise DatasetNotFoundError(dataset_name)

    def get_model(self, model_name):
        if not model_name:
            raise ValueError("No model name provided")

        for model in self.models:
            if model_name == model.name:
                return model

        raise ModelNotFoundError(model_name)

    def get_job(self, job_name):
        if not job_name:
            raise ValueError("No job name provided")

        for job in self.jobs:
            if (
                job_name == job.name
                or job_name == job.display_name
                or job_name == str(job.index)
            ):
                return job

        raise JobNotFoundError(job_name)

class AFML:
    """
    Handle project execution
    """

    def __init__(self, project_file):
        self.project = Project.load(project_file)

        os.makedirs(".afml", exist_ok=True)
        with open(".afml/project.pickle", 'wb') as serialized_file:
            pickle.dump(self.project, serialized_file)

    def run(self):
        for matrix in self.project.matrix:
            if len(matrix) > 0:
                cprint(f" {str(matrix):-<100}", 'white', 'on_magenta')
            for job in self.project.jobs:
                failed = job.run(self.project, matrix)
                if failed:
                    return True
                print()

        return False

    def run_job(self, job_name):
        job = self.project.get_job(job_name)

        for matrix in self.project.matrix:
            if len(matrix) > 0:
                cprint(f" {str(matrix):-<100}", 'white', 'on_magenta')

            failed = job.run(self.project, matrix)
            if failed:
                return True
            print()

        return False

def main():
    parser = ArgumentParser("AFML")
    parser.add_argument(
        '-p',
        '--project',
        dest='project_file',
        help="Project file",
        default="project.yml",
    )
    subparsers = parser.add_subparsers(dest='command')
    run_parser = subparsers.add_parser('run', help="Run project jobs")
    run_parser.add_argument(
        '-j', '--job',
        dest='job_name',  action='append',
        help="Job to execute"
    )

    args, _ = parser.parse_known_args()
    app = AFML(args.project_file)

    if args.command == 'run':
        if not args.job_name:
            app.run()
        else:
            for job_name in args.job_name:
                app.run_job(job_name)

if __name__ == '__main__':
    main()
