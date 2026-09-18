from backend.agents.terminal_agent import run_linux_command

print("--- LINUX COMMAND TEST ---")
print(run_linux_command.invoke({"commands": ["echo hello", "ls -la test_terminal_agent.py"]}))

print("--- COMMAND INJECTION TEST ---")
print(run_linux_command.invoke({"commands": ["echo hello; ls -la"]}))
