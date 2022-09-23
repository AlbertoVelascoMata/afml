import os
import json
from datetime import datetime

class Time:
    _instance = None

    def __init__(self):
        self.last_time = self.run_time = datetime.now()

        run_data_file = '.afml/run_data.json'
        if os.path.isfile(run_data_file):
            with open(run_data_file, 'r') as f:
                run_data = json.load(f)
            
            if 'last_time' in run_data:
                self.last_time = datetime.fromisoformat(run_data['last_time'])
        
        with open(run_data_file, 'w') as f:
            json.dump({
                'last_time': self.run_time.isoformat()
            }, f)

    @property
    def params(self):
        return {
            'time': self.run_time.strftime("%Y-%m-%d-%H-%M-%S"),
            'last_time': self.last_time.strftime("%Y-%m-%d-%H-%M-%S")
        }

    @staticmethod
    def get_params():
        t = Time.get_instance()
        return t.params

    @staticmethod
    def get_instance():
        if Time._instance is None:
            Time._instance = Time()
        
        return Time._instance
