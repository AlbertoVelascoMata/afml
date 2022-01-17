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

from .utils import Utils, ParamsFormatter
from .base import BaseObject
from .dataset import Dataset
from .model import Model
from .matrix import Matrix, MatrixInstance
from .context import RunContext

class Step(BaseObject):
    index = 0

    def __repr__(self):
        return f"Step({', '.join(f'{k}={repr(v)}' for k, v in {'name':self.display_name, 'script':self.script, **self.params}.items())})"
    
    def __init__(self, script, name=None, params={}):
        super().__init__(name, params)
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
            name=definition.get('name', None),
            script=definition['script'],
            params=definition.get('params', {})
        )

    def run(self, project, job, dataset=None, model=None, formatter=ParamsFormatter()):
        cprint(f"---- {self.display_name} [{self.display_script}] ----", 'blue')

        if self.script is None:
            cprint("WARNING: No script provided\n", 'yellow')
            return False

        formatter.update({'step': self})
        formatter.update(self.params)

        afml_context_file = f'.afml/ctx_job{job.index}_step{self.index}.pickle'
        ctx = RunContext(project, job, self, dataset, model, formatter)
        ctx.dump(afml_context_file)

        proc = subprocess.Popen(['python', self.script, '--afml-context', afml_context_file], shell=True, cwd=os.getcwd(), stderr=subprocess.PIPE)
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

class Job(BaseObject):
    index = 0

    def __repr__(self):
        return f"Job({', '.join(f'{k}={repr(v)}' for k, v in {'name':self.display_name, **self.params}.items())})"

    def __init__(self, steps : List[Step], name : str = None, dataset=None, model=None, matrix : Matrix = Matrix(), params : dict = {}, conditions : dict = {}):
        super().__init__(name, params)
        self.index = Job.index
        Job.index += 1
        self.steps = steps
        self.dataset_definition = dataset
        self.model_definition = model
        self.matrix = matrix
        self.conditions = conditions
    
    @property
    def display_name(self):
        return self.name if self.name else f'Job {self.index+1}'

    @staticmethod
    def parse(definition):
        if 'steps' not in definition:
            #raise Error
            return None

        return Job(
            name=definition.get('name', None),
            steps=[Step.parse(step) for step in definition['steps']],
            dataset=definition.get('dataset', None),
            model=definition.get('model', None),
            matrix = Matrix(**definition.get('matrix', {})),
            params=definition.get('params', {}),
            conditions=definition.get('if', {})
        )
    
    def get_step(self, step_name):
        pass

    def check_conditions(self, formatter):
        return all(Utils.check_condition(condition, formatter.format(expression))
                   for condition, expression in self.conditions.items())

    def run(self, project, project_matrix=MatrixInstance()):
        cprint(f"==== {self.display_name} ====", 'green')

        for job_matrix in self.matrix:
            if len(job_matrix) > 0:
                cprint(f" {str(job_matrix):-<100}", 'magenta', 'on_white')
            matrix = project_matrix.merge(job_matrix)

            formatter = ParamsFormatter(matrix=matrix)
            formatter.update(project.params)
            formatter.update({'job': self})
            
            dataset_definition = formatter.format(self.dataset_definition)
            if isinstance(dataset_definition, str):
                dataset = project.get_dataset(dataset_definition)
                if dataset is None:
                    cprint(f"ERROR: No dataset found by name '{dataset_definition}'", 'red')
                    exit(1)
            elif isinstance(dataset_definition, dict):
                dataset = Dataset.parse(dataset_definition)
            else:
                dataset = None

            model_definition = formatter.format(self.model_definition)
            if isinstance(model_definition, str):
                model = project.get_model(model_definition)
            elif isinstance(model_definition, dict):
                model = Model.parse(model_definition)
            else:
                model = None

            formatter.update({
                'dataset': dataset,
                'model': model
            })
            formatter.update(self.params)

            if not self.check_conditions(formatter):
                cprint(f"Skipping job, conditions not met", 'yellow')
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
        if not dataset_name: return None

        for dataset in self.datasets:
            if dataset_name == dataset.name:
                return dataset
        return None

    def get_model(self, model_name):
        if not model_name: return None

        for model in self.models:
            if model_name == model.name:
                return model
        return None
    
    def get_job(self, job_name):
        if not job_name: return None

        for job in self.jobs:
            if job_name == job.name or job_name == job.display_name or job_name == str(job.index):
                return job
        return None


class JobNotFoundError(LookupError): ...

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
        for job in self.project.jobs:
            for matrix in self.project.matrix:
                if len(matrix) > 0:
                    cprint(f" {str(matrix):-<100}", 'white', 'on_magenta')

                failed = job.run(self.project, matrix)
                if failed:
                    return True
                print()
        
        return False

    def run_job(self, job_name):
        job = self.project.get_job(job_name)
        if not job:
            raise JobNotFoundError(job_name)
        
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
