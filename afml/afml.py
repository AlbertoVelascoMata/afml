'''
    Automation Framework for Machine Learning
'''
from typing import List
import os
import yaml
import pickle
import subprocess
from argparse import ArgumentParser
from termcolor import cprint

from .utils.format import ParamsFormatter
from .base import BaseObject
from .runnable import RunnableObject
from .dataset import Dataset
from .model import Model
from .matrix import Matrix, MatrixInstance
from .context import RunContext

class DatasetNotFoundError(LookupError): ...
class ModelNotFoundError(LookupError): ...
class JobNotFoundError(LookupError): ...

class Step(RunnableObject):
    index = 0

    def __repr__(self):
        return f"Step({', '.join(f'{k}={repr(v)}' for k, v in {'name':self.display_name, 'script':self.script, **self.params}.items())})"
    
    def __init__(self, script : str, name : str = None, params : dict = {}, dataset=None, model=None,  conditions : dict = {}):
        super().__init__(name, params, dataset, model, conditions)
        self.index = Step.index
        Step.index += 1
        self.script = script
    
    @property
    def display_name(self):
        return self.name if self.name else f'Step {self.index+1}'
    
    @property
    def display_script(self):
        return self.script if self.script else '<empty>'

    @staticmethod
    def parse(definition):
        if 'script' not in definition:
            #raise Error
            return None
        
        return Step(
            script=definition['script'],
            name=definition.get('name'),
            params=definition.get('params') or {},
            dataset=definition.get('dataset'),
            model=definition.get('model'),
            conditions=definition.get('if') or {}
        )

    def run(self, project, job, dataset=None, model=None, formatter=ParamsFormatter()):
        cprint(f"---- {self.display_name} [{self.display_script}] ----", 'blue')

        if self.script is None:
            cprint("WARNING: No script provided\n", 'yellow')
            return False

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
            cprint(f"Skipping step", 'yellow')
            return False

        afml_context_file = f'.afml/ctx_job{job.index}_step{self.index}.pickle'
        ctx = RunContext(project, job, self, dataset, model, formatter)
        ctx.dump(afml_context_file)

        proc = subprocess.Popen(f'python "{self.script}" --afml-context "{afml_context_file}"', shell=True, cwd=os.getcwd(), stderr=subprocess.PIPE)
        while True:
            output = proc.stderr.readline()
            if output:
                cprint(output.decode('utf-8', errors='replace'), 'yellow', end='')
            
            if proc.poll() is not None:
                break

        os.remove(afml_context_file)

        if proc.poll() != 0:
            cprint('ERROR: Step execution failed!', 'red')
            return True
        
        return False

class Job(RunnableObject):
    index = 0

    def __repr__(self):
        return f"Job({', '.join(f'{k}={repr(v)}' for k, v in {'name':self.display_name, **self.params}.items())})"

    def __init__(self, steps : List[Step], name : str = None, params : dict = {}, dataset=None, model=None,  conditions : dict = {}, matrix : Matrix = Matrix()):
        super().__init__(name, params, dataset, model, conditions)
        self.index = Job.index
        Job.index += 1
        self.steps = steps
        self.matrix = matrix
    
    @property
    def display_name(self):
        return self.name if self.name else f'Job {self.index+1}'

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
                cprint(f"Skipping job", 'yellow')
                return False
            
            for step in self.steps:
                failed = step.run(project, self, dataset, model, formatter.copy())
                if failed:
                    return True
                print()
        
        return False


class Project(BaseObject):
    def __repr__(self):
        return f"Project({', '.join(f'{k}={repr(v)}' for k, v in self.params.items())})"

    def __init__(self, datasets : List[Dataset] = [], models : List[Model] = [], jobs : List[Job] = [], matrix : Matrix = Matrix(), params : dict = {}):
        super().__init__(params=params)
        self.datasets : List[Dataset] = datasets
        self.models : List[Model] = models
        self.jobs : List[Job] = jobs
        self.matrix : Matrix = matrix

    @staticmethod
    def load(file):
        with open(file, 'r') as f:
            definition = yaml.safe_load(f)

        return Project(
            datasets = [Dataset.parse(dataset) for dataset in definition.get('datasets', [])],
            models = [Model.parse(model) for model in definition.get('models', [])],
            jobs = [Job.parse(job) for job in definition.get('jobs', [])],
            matrix = Matrix(**definition.get('matrix', {})),
            params = definition.get('params', {})
        )

    def get_dataset(self, dataset_name):
        if not dataset_name:
            raise ValueError(f"No dataset name provided")

        for dataset in self.datasets:
            if dataset_name == dataset.name:
                return dataset
        
        raise DatasetNotFoundError(dataset_name)

    def get_model(self, model_name):
        if not model_name:
            raise ValueError(f"No model name provided")

        for model in self.models:
            if model_name == model.name:
                return model
        
        raise ModelNotFoundError(model_name)
    
    def get_job(self, job_name):
        if not job_name:
            raise ValueError(f"No job name provided")

        for job in self.jobs:
            if job_name == job.name or job_name == job.display_name or job_name == str(job.index):
                return job

        raise JobNotFoundError(job_name)


class AFML:
    '''
        Handle project execution
    '''
    def __init__(self, project_file):
        self.project = Project.load(project_file)
        
        os.makedirs('.afml', exist_ok=True)
        with open('.afml/project.pickle', 'wb') as f:
            pickle.dump(self.project, f)

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
    parser = ArgumentParser('AFML')
    parser.add_argument('-p', '--project', dest='project_file', help="Project file", default='project.yml')
    subparsers = parser.add_subparsers(dest='command')
    run_parser = subparsers.add_parser('run', help="Run project jobs")
    run_parser.add_argument('-j', '--job', dest='job_name', help="Job to execute", action='append')

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
