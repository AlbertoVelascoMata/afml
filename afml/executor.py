import os
import subprocess
from abc import ABC, abstractmethod

from .context import RunContext
from .utils.format import ParamsFormatter


def get_executor(definition: dict) -> 'Executor':
    if 'mode' in definition and 'mode' != 'auto':
        executor = {
            'python': PythonExecutor,
            'python-module': PythonExecutor,
            'shell': ShellExecutor
        }.get(definition['mode'], None)
        if executor is None:
            #raise Error
            return None
        return executor.parse(definition)

    # Try to guess executor, mode='auto'
    if (
        any(
            key in definition
            for key in ('python', 'python-module')
        )
        or (
            'script' in definition
            and definition['script'].endswith('.py')
        )
    ):
        return PythonExecutor.parse(definition)
    
    if (
        any(
            key in definition
            for key in ('shell', 'command')
        )
        or (
            'script' in definition
            and (
                definition['script'].endswith('.sh')
                or definition['script'].endswith('.bat')
            )
        )
    ):
        return ShellExecutor.parse(definition)
    
    #raise Error
    return None

class Executor(ABC):
    class ExecutionWrapper:
        def __init__(self, executor_run):
            self.run_func = executor_run
            self.exit_code = False
        
        def __iter__(self):
            self.exit_code = yield from self.run_func
            return self.exit_code

    def __init__(self, **formatable_vars):
        self._formatable_vars = formatable_vars

    @staticmethod
    @abstractmethod
    def parse(definition: dict): ...

    def __repr__(self):
        args = ', '.join(
            f'{k}={repr(v)}'
            for k, v in self.__dict__.items()
        )
        return f"{self.__class__.__name__}({args})"

    def __str__(self):
        return self.__class__.__name__

    @abstractmethod
    def run(self, ctx: RunContext, **kwargs): ...

    def start(self, ctx: RunContext, formatter: ParamsFormatter):
        return Executor.ExecutionWrapper(self.run(
            ctx,
            **formatter.format(self._formatable_vars)
        ))

class PythonExecutor(Executor):
    DEFAULT_INTERPRETER = 'python'

    def __init__(
        self,
        script: str,
        as_module: bool = False,
        interpreter=DEFAULT_INTERPRETER
    ):
        Executor.__init__(self)
        if as_module and script.startswith('-m'):
            self.script = script[2:].strip()
        else:
            self.script = script
        if not self.script:
            pass #raise Error

        self.as_module = as_module
        self.interpreter = interpreter

    @staticmethod
    def parse(definition):
        # Check that this is the selected executor
        mode = definition.get('mode', 'auto')
        if mode not in ('auto', 'python', 'python-module'):
            #raise Error
            return None

        # Check if there are incompatible params
        found_keys = [
            key
            for key in ('python', 'python-module', 'script')
            if key in definition
        ]
        if len(found_keys) > 1:
            #raise Error(f"Found multiple keys related to the Python executor: {', '.join(found_keys)}")
            return None

        # Check if a custom interpreter was defined
        interpreter = str(definition.get('python-interpreter',
                                         PythonExecutor.DEFAULT_INTERPRETER))

        # The 'python' key is allowed in any mode
        if 'python' in definition:
            script = str(definition['python'])
            return PythonExecutor(script,
                                  mode == 'python-module',
                                  interpreter)

        # The 'python-module' key will enfoce to run the
        # script as a module, no matter what mode is selected
        if 'python-module' in definition:
            module = str(definition['python-module'])
            return PythonExecutor(module, True, interpreter)

        # The 'script' key is generic. The module detection
        # depends on 'mode', the '-m' preffix and the 'script'
        # content format
        if 'script' in definition:
            script = str(definition['script'])
            if (
                mode == 'python-module'
                or script.startswith('-m')
                or (
                    mode == 'auto'
                    and not script.endswith('.py')
                    and '/' not in script
                    and '\\' not in script
                )
            ):
                return PythonExecutor(script, True, interpreter)

            return PythonExecutor(script, False, interpreter)

        #raise Error
        return None
    
    def __repr__(self):
        return (
            "Python("
            f"{'module' if self.as_module else 'script'}="
            f"{self.script}, "
            f"interpreter={self.interpreter})"
        )

    def __str__(self):
        if self.interpreter != PythonExecutor.DEFAULT_INTERPRETER:
            return f"{self.interpreter} {self.script}"
        return self.script

    def run(self, ctx: RunContext, **kwargs):
        context_file = f".afml/{ctx.id}.pickle"
        ctx.dump(context_file)

        with subprocess.Popen(
            ' '.join((
                self.interpreter,
                '-m' if self.as_module else '',
                f'"{self.script}"',
                f'--afml-context "{context_file}"'
            )),
            shell=True,
            cwd=os.getcwd(),
            stderr=subprocess.PIPE,
        ) as proc:
            while True:
                output = proc.stderr.readline()
                if output:
                    yield output.decode('utf-8', errors='replace')

                if proc.poll() is not None:
                    break

            os.remove(context_file)
            return proc.poll()

class ShellExecutor(Executor):
    def __init__(self, command: str, args: str = ''):
        Executor.__init__(self, args=args)
        if not command:
            pass #raise Error
        self.command = command

    @staticmethod
    def parse(definition):
        # Check that this is the selected executor
        mode = definition.get('mode', 'auto')
        if mode not in ('auto', 'shell'):
            #raise Error
            return None

        # Check if there are incompatible params
        found_keys = [
            key
            for key in ('shell', 'command', 'script')
            if key in definition
        ]
        if len(found_keys) > 1:
            #raise Error(f"Found multiple keys related to the Shell executor: {', '.join(found_keys)}")
            return None

        # Check if there are extra params
        args = str(definition.get('shell-args', ''))

        # Get command by any of the allowed keys
        command = next((
            str(definition[key])
            for key in ('shell', 'command', 'script')
            if key in definition
        ), None)
        if command is not None:
            return ShellExecutor(command, args)

        #raise Error
        return None

    def __repr__(self):
        return f"Shell(cmd={self.command})"

    def __str__(self):
        return self.command.strip().split(' ')[0]

    def run(self, ctx: RunContext, **kwargs):
        with subprocess.Popen(
            ' '.join((self.command, kwargs.get('args', ''))),
            shell=True,
            cwd=os.getcwd(),
            stderr=subprocess.PIPE,
        ) as proc:
            while True:
                output = proc.stderr.readline()
                if output:
                    yield output.decode('utf-8', errors='replace')

                if proc.poll() is not None:
                    break

            return proc.poll()
