'''
    Automation Framework for Machine Learning
'''
import os
import yaml
import json
import pickle
import subprocess
from datetime import datetime
from termcolor import cprint

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
    for key in params:
        if isinstance(params[key], str):
            params[key] = params[key].format(**key_dict, **params,
                                             time=datetime.now().strftime("%d_%m_%Y_%H_%M_%S"))
    
    return params

def main():
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

            step_params = format_params(step.get('params', {}),
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
