class Task(object):
    """task to do
    """
    def __init__(self):
        """construct
        """
        self.name = None
        self.kwargs = None

class ExecfileCommand(object):
    """eval command
    """
    task_name = 'execfile'
    def run(self, script=None):
        """run given scritp
        """
        return exec(compile(open(script).read(), script, 'exec'), globals(), locals() )

class EvalCommand(object):
    """eval command
    """
    task_name = 'eval'

    def run(self, code=None):
        """run given scritp
        """
        return eval(code)

class CommandRunner(object):
    """system that executes blender commands based on given data
    """
    def __init__(self):
        """construct
        """
        self.task = None

    def run(self):
        """run commander
        """
        command_classes = [
            ExecfileCommand,
            EvalCommand
        ]

        for command_class in command_classes:
            if self.task.name == command_class.task_name:
                command = command_class()
                return command.run(**self.task.kwargs)

task = Task()
task.name = 'execfile'
task.kwargs = {'script' : '/home/sven.fr/grid_tools/gsnippets/python/01_hello_world.py'}

task.name = 'eval'
task.kwargs = {'code' : '5 + 2'}

commander = CommandRunner()
commander.task = task
results = commander.run()
print(results)