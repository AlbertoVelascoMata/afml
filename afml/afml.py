'''
    Automation Framework for Machine Learning
'''
import os
from typing import List
import yaml
import json
import pickle
import subprocess
from datetime import datetime
from termcolor import cprint

from .model import Model

class Step:
    def __init__(self, script, name=None, params={}):
        self._name = name
        self.script = script
        self._params = params

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

class Job:
    def __init__(self, steps : List[Step], name : str = None, data=None, model=None, params : dict = {}):
        self._name = name
        self.steps = steps
        self._params = params

    @staticmethod
    def parse(definition):
        if 'steps' not in definition:
            #raise Error
            return None

        return Job(
            name=definition.get('name', None),
            steps=[Step.parse(step) for step in definition['steps']],
            data=definition.get('data', None),
            model=definition.get('model', None),
            params=definition.get('params', {})
        )

class Dataset:
    def __init__(self, folder, name : str = None):
        self._name = name
        self.folder = folder
    
    @staticmethod
    def parse(definition):
        if 'folder' not in definition:
            #raise Error
            return None
        
        return Dataset(
            name=definition.get('name', None),
            folder=definition['folder']
        )

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

class AFML:
    '''
        Handle project execution
    '''
    def __init__(self):
        self.project = Project.load("project.yml")
        
        os.makedirs('.afml', exist_ok=True)
        with open('.afml/project.pickle', 'wb') as f:
            pickle.dump(self.project, f)
        
        print(self.project)
        print([e for e in self.project.datasets])
        print([e for e in self.project.models])
        print([e for e in self.project.jobs])

    def run(self):
        for i, job in enumerate(self.project.jobs):
            for j, step in enumerate(job.steps):
                #step_name = get_step_name(step, j+1)
                #script_path = get_step_script(step)

                #params = {'test_param': 'value'}
                with open('.afml/step_params.pickle', 'wb') as f:
                    pickle.dump({**self.project.params, **job._params, **step._params}, f)

                proc = subprocess.Popen(['python', step.script], shell=True, cwd=os.getcwd(), stderr=subprocess.PIPE)
                while True:
                    output = proc.stderr.readline()
                    if output:
                        cprint(output.decode('utf-8'), 'yellow', end='')
                    
                    if proc.poll() is not None:
                        break

                if proc.poll() != 0:
                    cprint('ERROR: Step execution failed!', 'red')
                    exit(1)

PARAMS_FILE = 'step_params.pickle'

def initialize():
    with open(PARAMS_FILE, 'rb') as f:
        return pickle.load(f)

def save_params(params):
    with open(PARAMS_FILE, 'wb') as f:
        pickle.dump(params, f)

def delete_params():
    os.remove(PARAMS_FILE)

def get_step_name(step, index):
    name = step.get('name', None)
    if name is None or len(name) == 0:
        name = f'Step {index}'
    return name

def get_step_script(step):
    if 'script' in step and len(step['script']) > 0:
        return step['script']
    return None

def format_params(params, **key_dict):
    if not params:
        return {}
    for key in params:
        if isinstance(params[key], str):
            params[key] = params[key].format(**key_dict, **params,
                                             time=datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
    
    return params

def main():
    app = AFML()
    app.run()
    exit()
    with open("project.yml", 'r') as f:
        project = yaml.safe_load(f)

    jobs = project.pop('jobs', [])
    project_params = project

    for i, job in enumerate(jobs):
        job_name = job.get('name', f'Job {i+1}')
        cprint(f"==== {job_name} ====", 'green')

        steps = job.pop('steps', [])
        job_params = format_params(job.get('params', {}),
                                   job=job_name)

        for j, step in enumerate(steps):
            step_name = get_step_name(step, j+1)
            script_path = get_step_script(step)

            cprint(f"---- {step_name} [{'<empty>' if script_path is None else script_path}] ----", 'blue')

            if script_path is None:
                cprint("WARNING: No script provided\n", 'yellow')
                continue

            step_params = format_params(step.get('params', None),
                                        job=job_name,
                                        **job_params,
                                        step=step_name)

            params = project_params.copy()
            params.update(job_params)
            params.update(step_params)
            save_params(params)

            proc = subprocess.Popen(['python', script_path], shell=True, cwd=os.getcwd(), stderr=subprocess.PIPE)
            while True:
                output = proc.stderr.readline()
                if output:
                    cprint(output.decode('utf-8'), 'yellow', end='')
                
                if proc.poll() is not None:
                    break

            delete_params()

            if proc.poll() != 0:
                cprint('ERROR: Step execution failed!', 'red')
                exit(1)
            
            print()
        
        print()

if __name__ == '__main__':
    main()
