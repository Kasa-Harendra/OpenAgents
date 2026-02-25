---
name: terminal-execution
description: Safe execution of PowerShell and CMD commands with validation, error handling, and user-friendly output formatting
license: MIT
compatibility: Windows PowerShell, CMD
metadata:
  author: OpenAgents
  version: "1.0"
  allowed-tools: run_command
---

# terminal-execution

## Overview

This skill provides comprehensive guidance for executing Windows terminal commands safely and effectively. It covers PowerShell and CMD command execution with safety validation, error handling, and structured output formatting.

## Core Principles

1. **Safety First**: Validate destructive commands before execution
2. **PowerShell Default**: Prefer PowerShell over CMD for reliability
3. **Absolute Paths**: Use full paths when available
4. **Clear Output**: Provide structured, user-friendly responses
5. **Error Explanation**: Explain errors in plain language with suggested fixes

## Instructions

### Step 1: Validate Command Safety

Before executing any command, assess its safety level:

#### 🔴 High-Risk Commands (Note but Execute)

- **File deletion**: `rm`, `del`, `Remove-Item`
- **Directory deletion**: `rmdir`, `Remove-Item -Recurse`
- **System operations**: `shutdown`, `restart`, `format`
- **Bulk operations**: Wildcards with delete (`*.txt`)

**Action**: Note the risk in output, proceed with execution

#### 🟡 Medium-Risk Commands (Validate Parameters)

- **File moves**: `move`, `Move-Item`
- **Permission changes**: `icacls`, `Set-Acl`
- **Process termination**: `Stop-Process`, `taskkill`

**Action**: Verify parameters, execute

#### 🟢 Low-Risk Commands (Execute Directly)

- **Read operations**: `dir`, `Get-ChildItem`, `cat`, `type`
- **System info**: `systeminfo`, `Get-Process`, `hostname`
- **Development tools**: `git`, `npm`, `python --version`

**Action**: Execute immediately

---

### Step 2: Format Command for Execution

#### PowerShell (Preferred)

Use PowerShell cmdlets for better structure:

```powershell
Get-ChildItem -Path C:\Users\Public
Get-Process | Select-Object -First 10
```

#### CMD (When Necessary)

Use for specific CMD-only commands:

```cmd
dir C:\Windows
ipconfig /all
```

#### Path Handling

- **Use absolute paths** when provided: `C:\Users\User\Documents\file.txt`
- **Use relative paths** only when working directory is clear: `.\file.txt`
- **Escape special characters** in paths: Use quotes for paths with spaces

---

### Step 3: Execute Command

Use the `run_command` tool:

```json
{
  "tool": "run_command",
  "params": {
    "command": "Get-ChildItem -Path C:\\Users\\Public"
  }
}
```

The tool returns:

- **stdout**: Standard output
- **stderr**: Standard error
- **returncode**: Exit code (0 = success, non-zero = error)

---

### Step 4: Format Output

Present results in structured format:

#### Successful Execution (returncode = 0)

```
Command: [command executed]
Exit Code: 0

Output:
[stdout content]
```

#### Failed Execution (returncode ≠ 0)

```
Command: [command executed]
Exit Code: [code]

Errors:
[stderr content]

Explanation:
[User-friendly explanation of what went wrong]

Suggested Fix:
[Actionable suggestion to resolve the issue]
```

---

### Step 5: Explain Errors (If Any)

For common errors, provide clear explanations:

#### Error: "Command not found"

**Explanation**: The command or program is not installed or not in PATH
**Fix**: Install the program or provide full path to executable

#### Error: "Access denied"

**Explanation**: Insufficient permissions to execute command
**Fix**: Run terminal as Administrator or check file permissions

#### Error: "File not found"

**Explanation**: The specified file or directory doesn't exist
**Fix**: Verify the path, check for typos, use absolute path

#### Error: "Syntax error"

**Explanation**: Command syntax is incorrect
**Fix**: Check command syntax, use `Get-Help [command]` for PowerShell

---

## Common Commands

### File System Operations

**List files**:

```powershell
Get-ChildItem -Path C:\Users\Public
```

**Read file**:

```powershell
Get-Content -Path C:\file.txt
```

**Create directory**:

```powershell
New-Item -ItemType Directory -Path C:\NewFolder
```

**Delete file** (⚠️ Destructive):

```powershell
Remove-Item -Path C:\file.txt
```

### System Information

**Get OS info**:

```powershell
systeminfo
Get-ComputerInfo
```

**List running processes**:

```powershell
Get-Process | Select-Object -First 20
```

**Check disk space**:

```powershell
Get-PSDrive -PSProvider FileSystem
```

### Development Tools

**Check Python version**:

```powershell
python --version
```

**Git status**:

```powershell
git status
```

**NPM install**:

```powershell
npm install
```

**Run Python script**:

```powershell
python script.py
```

---

## Safety Examples

### Example 1: Safe File Listing

**Request**: "List files in D: drive"

**Execution**:

```
Safety Check: ✅ Read operation - safe
Command: Get-ChildItem -Path D:\

Exit Code: 0

Output:
Directory: D:\

Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d----          1/15/2026   3:30 PM                Projects
d----          1/10/2026   2:15 PM                Documents
-a---          1/12/2026   1:45 PM         524288 data.xlsx
```

---

### Example 2: Destructive Command with Warning

**Request**: "Delete temp.txt from desktop"

**Execution**:

```
Safety Check: ⚠️ DESTRUCTIVE - File deletion
Command: Remove-Item -Path C:\Users\User\Desktop\temp.txt

Exit Code: 0

Output:
File successfully deleted.

Note: This was a destructive operation. The file cannot be recovered from Recycle Bin if deleted via PowerShell.
```

---

### Example 3: Error with Explanation

**Request**: "Run nonexistent-command"

**Execution**:

```
Command: nonexistent-command

Exit Code: 1

Errors:
nonexistent-command : The term 'nonexistent-command' is not recognized as the name of a cmdlet, function, script file, or operable program.

Explanation:
The command 'nonexistent-command' is not installed on this system or is not in the system PATH.

Suggested Fix:
1. Verify the command name (check for typos)
2. Install the required program if missing
3. Add the program's directory to system PATH
4. Use absolute path to the executable
```

---

## PowerShell vs CMD

### When to Use PowerShell (Preferred)

- **Object-based output**: Rich, structured data
- **Advanced filtering**: Pipeline operations
- **Modern syntax**: Readable cmdlets
- **Better error messages**: Detailed error information

### When to Use CMD

- **Legacy scripts**: Existing .bat files
- **Specific CMD commands**: `ipconfig`, `netstat`
- **Compatibility**: Older systems

---

## Error Handling Patterns

### Pattern 1: Path Not Found

```
Error: Cannot find path 'C:\nonexistent\file.txt'
Explanation: The specified path does not exist
Fix: Verify the path exists, check spelling, create parent directories
```

### Pattern 2: Permission Denied

```
Error: Access to the path is denied
Explanation: Current user lacks permissions to access this resource
Fix: Run PowerShell as Administrator or request permissions from owner
```

### Pattern 3: Process Not Found

```
Error: Cannot find a process with the name "nonexistent"
Explanation: No running process matches the specified name
Fix: List running processes with Get-Process to find correct name
```

---

## Best Practices

1. **Use PowerShell Cmdlets**: Prefer `Get-ChildItem` over `dir`
2. **Validate Paths**: Check paths exist before operations
3. **Quote Paths with Spaces**: Use quotes: `"C:\Program Files\app.exe"`
4. **Test First**: Use `-WhatIf` for destructive operations in PowerShell
5. **Provide Full Context**: Include working directory in output

---

## Advanced Examples

### Example 4: Git Operations

**Request**: "Check git status"

**Execution**:

```
Safety Check: ✅ Read operation
Command: git status

Exit Code: 0

Output:
On branch main
Your branch is up to date with 'origin/main'.

nothing to commit, working tree clean
```

---

### Example 5: Process Management

**Request**: "List top 5 processes by CPU usage"

**Execution**:

```
Safety Check: ✅ Read operation
Command: Get-Process | Sort-Object CPU -Descending | Select-Object -First 5

Exit Code: 0

Output:
 NPM(K)    PM(M)      WS(M)     CPU(s)      Id  SI ProcessName
 ------    -----      -----     ------      --  -- -----------
    125   234.56     456.78      123.45    1234   1 chrome
     89   178.23     345.67       89.12    5678   1 code
     45    123.45     234.56       67.89    9012   1 node
```

---

## Troubleshooting

**Q: Command works in terminal but not via agent**
**A**: Check for interactive prompts, use non-interactive flags, provide all inputs

**Q: Permission errors on file operations**
**A**: Verify user permissions, use Administrator terminal if needed

**Q: PowerShell not found**
**A**: Verify PowerShell is installed: `Get-Host` or use CMD as fallback

**Q: Output too long / truncated**
**A**: Use pagination (`Select-Object -First N`) or save to file
