import subprocess
import shlex
import platform

def test_cmd(cmd):
    if isinstance(cmd, str):
        cmd = shlex.split(cmd)
    try:
        completed = subprocess.run(cmd, shell=False, capture_output=True, text=True)
        print("OUT:", completed.stdout.strip())
        print("ERR:", completed.stderr.strip())
    except Exception as e:
        print("EXCEPTION:", e)

print("LINUX")
test_cmd("echo hello world")
test_cmd("ls -la")

print("WINDOWS")
# simulate a windows command
