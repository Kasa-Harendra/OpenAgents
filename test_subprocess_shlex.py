import subprocess
import shlex

def run_linux_command(commands: list):
    results = []
    for cmd in commands:
        try:
            if isinstance(cmd, str):
                cmd = shlex.split(cmd)
            completed = subprocess.run(cmd, shell=False, capture_output=True, text=True)
            output = completed.stdout + completed.stderr
        except Exception as e:
            output = str(e)
        results.append(output)
    return "\n".join(results)

print(run_linux_command(["echo hello", "ls -la test_subprocess.py"]))
