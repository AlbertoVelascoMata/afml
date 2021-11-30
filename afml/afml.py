'''
    Automation Framework for Machine Learning
'''
from typing import List
import os
import yaml
import pickle
import subprocess
from termcolor import cprint

from .base import BaseObject
from .dataset import Dataset
from .model import Model
from .context import RunContext

class Step(BaseObject):
    index = 0
    
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
    
    def run(self, project, job):
        cprint(f"---- {self.display_name} [{self.display_script}] ----", 'blue')

        if self.script is None:
            cprint("WARNING: No script provided\n", 'yellow')
            return False

        afml_context_file = f'.afml/ctx_job{job.index}_step{self.index}.pickle'
        ctx = RunContext(project, job, self,
                         dataset=project.get_dataset(job.dataset_name),
                         model=project.get_model(job.model_name))
        ctx.dump(afml_context_file)

        proc = subprocess.Popen(['python', self.script, '--afml-context', afml_context_file], shell=True, cwd=os.getcwd(), stderr=subprocess.PIPE)
        while True:
            output = proc.stderr.readline()
            if output:
                cprint(output.decode('utf-8'), 'yellow', end='')
            
            if proc.poll() is not None:
                break

        os.remove(afml_context_file)

        if proc.poll() != 0:
            cprint('ERROR: Step execution failed!', 'red')
            return True
        
        return False

class Job(BaseObject):
    index = 0

    def __init__(self, steps : List[Step], name : str = None, dataset=None, model=None, params : dict = {}):
        super().__init__(name, params)
        self.index = Job.index
        Job.index += 1
        self.steps = steps
        self.dataset_name = dataset
        self.model_name = model
    
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
            params=definition.get('params', {})
        )
    
    def get_step(self, step_name):
        pass

    def run(self, project):
        cprint(f"==== {self.display_name} ====", 'green')
        dataset = project.get_dataset(self.dataset_name)
        model = project.get_model(self.model_name)

        for step in self.steps:
            failed = step.run(project, self)
            if failed:
                return True
            print()
        
        return False

class Project:
    def __init__(self, datasets : List[Dataset] = [], models : List[Model] = [], jobs : List[Job] = [], params : dict = {}):
        self.datasets : List[Dataset] = datasets
        self.models : List[Model] = models
        self.jobs : List[Job] = jobs
        self.params = params

    @staticmethod
    def load(file):
        with open("project.yml", 'r') as f:
            definition = yaml.safe_load(f)

        return Project(
            datasets = [Dataset.parse(dataset) for dataset in definition.get('datasets', [])],
            models = [Model.parse(model) for model in definition.get('models', [])],
            jobs = [Job.parse(job) for job in definition.get('jobs', [])],
            params = definition.get('params', {}),
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
        pass

class AFML:
    '''
        Handle project execution
    '''
    def __init__(self):
        self.project = Project.load("project.yml")
        
        os.makedirs('.afml', exist_ok=True)
        with open('.afml/project.pickle', 'wb') as f:
            pickle.dump(self.project, f)

    def run(self):
        for job in self.project.jobs:
            failed = job.run(self.project)
            if failed:
                return True
            print()
        
        return False


def main():
    app = AFML()
    app.run()
    exit()

if __name__ == '__main__':
    main()
