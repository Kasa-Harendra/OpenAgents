---
name: filesystem-management
description: Safe file and directory operations with path validation, size awareness, encoding handling, and comprehensive error management
license: MIT
compatibility: Local filesystem access
metadata:
  author: OpenAgents
  version: "1.0"
  allowed-tools: list_files, read_file, write_file, move_file, delete_file, search_files
---

# filesystem-management

## Overview

This skill provides comprehensive guidance for safe and efficient file system operations. It covers listing, reading, writing, moving, and deleting files with proper validation, size awareness, and error handling.

## Core Principles

1. **Validate First**: Check paths exist before operations
2. **Size Awareness**: Warn before reading large files
3. **Safety Protocols**: Note destructive operations
4. **Encoding Handling**: Default to UTF-8, detect when needed
5. **Clear Feedback**: Provide descriptive messages

## Instructions

### Step 1: Validate Path

Before any operation, validate the target path:

#### Path Existence Check

```python
# Check if path exists
if not os.path.exists(path):
    return f"⚠️ Path does not exist: {path}"
```

#### Path Type Check

```python
# Verify it's the right type
is_file = os.path.isfile(path)
is_dir = os.path.isdir(path)
```

#### Permission Check

```python
# Check read/write permissions
can_read = os.access(path, os.R_OK)
can_write = os.access(path, os.W_OK)
```

**Output**: Proceed if valid, warn user if issues found

---

### Step 2: Assess Operation Safety

Evaluate the requested operation:

#### 🟢 Safe Operations

- **list_files**: List directory contents
- **read_file**: Read file contents
- **search_files**: Find files by pattern

**Action**: Execute directly after path validation

#### 🟡 Moderate Operations

- **write_file**: Create or update files
- **move_file**: Relocate files/directories

**Action**: Validate destination, create parent dirs if needed

#### 🔴 Destructive Operations

- **delete_file**: Permanently remove files

**Action**: Note the destructive nature in output, execute

---

### Step 3: Check File Size (for read operations)

Before reading a file, check its size:

#### Size Categories

- **< 1 MB**: ✅ Read safely
- **1-10 MB**: ⚠️ Warn user, proceed
- **> 10 MB**: 🚫 Warn strongly, suggest alternatives

#### Size Check Code

```python
size_bytes = os.path.getsize(path)
size_mb = size_bytes / (1024 * 1024)

if size_mb > 10:
    return f"⚠️ Large file ({size_mb:.2f} MB). Consider reading in chunks or using a different tool."
elif size_mb > 1:
    print(f"Note: Reading {size_mb:.2f} MB file...")
```

---

### Step 4: Execute File Operation

Use appropriate tool based on operation:

#### List Files

```json
{
  "tool": "list_files",
  "params": {
    "path": "C:\\Users\\User\\Documents"
  }
}
```

**Output**: Include file sizes in human-readable format (KB, MB, GB)

#### Read File

```json
{
  "tool": "read_file",
  "params": {
    "path": "C:\\Users\\User\\config.json",
    "encoding": "utf-8"
  }
}
```

**Encoding Priority**:

1. UTF-8 (default)
2. Detect from BOM if present
3. Try latin-1 as fallback

#### Write File

```json
{
  "tool": "write_file",
  "params": {
    "path": "C:\\Users\\User\\output.txt",
    "content": "File contents here",
    "encoding": "utf-8"
  }
}
```

**Important**: Create parent directories automatically if they don't exist

#### Move File

```json
{
  "tool": "move_file",
  "params": {
    "src": "C:\\Users\\User\\old\\file.txt",
    "dst": "C:\\Users\\User\\new\\file.txt"
  }
}
```

#### Delete File

```json
{
  "tool": "delete_file",
  "params": {
    "path": "C:\\Users\\User\\temp.txt"
  }
}
```

---

### Step 5: Provide Clear Feedback

Format output based on operation result:

#### Success Format

```
✅ [Operation] successful

Details:
- Path: [path]
- [Operation-specific details]
```

#### Error Format

```
❌ [Operation] failed

Error: [error message]

Explanation: [user-friendly explanation]

Suggested Fix:
- [Actionable suggestion 1]
- [Actionable suggestion 2]
```

---

## Common Operations

### List Directory Contents

**Request**: "List files in Documents folder"

**Execution**:

```
Operation: list_files
Path: C:\Users\User\Documents

✅ Found 15 items:

Directories:
- Projects (5 items)
- Work Documents (12 items)

Files:
- notes.txt (2.5 KB)
- report.pdf (1.3 MB)
- data.xlsx (524 KB)
- config.json (1.2 KB)
```

---

### Read File with Size Warning

**Request**: "Read large-data.csv"

**Execution**:

```
⚠️ Large file detected: 12.5 MB

Operation: read_file
Path: C:\Users\User\large-data.csv

Note: This file is large and may take time to process.
Consider using specialized CSV tools or reading in chunks.

Suggested alternatives:
- Use pandas: pd.read_csv('large-data.csv', chunksize=1000)
- Use Excel to open the file
- Process specific rows only

Proceed with read? Attempting...
```

---

### Create File with Auto-Directory Creation

**Request**: "Write config to new/folder/config.json"

**Execution**:

```
Operation: write_file
Path: C:\Users\User\new\folder\config.json

Note: Parent directories don't exist. Creating...
- Created: C:\Users\User\new
- Created: C:\Users\User\new\folder

✅ File written successfully

Details:
- Path: C:\Users\User\new\folder\config.json
- Size: 345 bytes
- Encoding: UTF-8
```

---

### Delete File with Warning

**Request**: "Delete temp-cache.txt"

**Execution**:

```
⚠️ DESTRUCTIVE OPERATION

Operation: delete_file
Path: C:\Users\User\temp-cache.txt

✅ File deleted successfully

Note: This operation is permanent. The file cannot be recovered from Recycle Bin.
```

---

## Error Handling

### Error 1: File Not Found

**Scenario**: Reading non-existent file

**Response**:

```
❌ File not found

Path: C:\Users\User\missing.txt

Explanation:
The specified file does not exist at the given path.

Suggested Fix:
- Verify the filename and path (check for typos)
- Use absolute path instead of relative path
- List directory contents to find the correct file

Similar files found:
- C:\Users\User\missing_old.txt
- C:\Users\User\Documents\missing.txt
```

---

### Error 2: Permission Denied

**Scenario**: Writing to protected directory

**Response**:

```
❌ Permission denied

Path: C:\Windows\System32\config.sys

Explanation:
Current user lacks write permissions for this location.
System directories require administrator access.

Suggested Fix:
- Use a different directory (e.g., user's Documents folder)
- Run application as Administrator
- Request permissions from system administrator
```

---

### Error 3: Encoding Error

**Scenario**: Reading file with incorrect encoding

**Response**:

```
❌ Encoding error

Path: C:\Users\User\legacy-file.txt

Explanation:
File encoding doesn't match UTF-8 (default).
File may use different encoding (e.g., latin-1, windows-1252).

Suggested Fix:
- Try reading with encoding='latin-1'
- Try reading with encoding='windows-1252'
- Use file encoding detection tools
- Open in text editor to check encoding

Attempting auto-detection...
Detected: windows-1252
Retrying with detected encoding...
```

---

### Error 4: Directory Not Empty

**Scenario**: Deleting non-empty directory

**Response**:

```
❌ Cannot delete directory

Path: C:\Users\User\project

Explanation:
Directory contains files and subdirectories.
Cannot delete non-empty directory with delete_file.

Contents:
- 15 files
- 3 subdirectories

Suggested Fix:
- Delete files individually first
- Use recursive delete (if available)
- Move contents elsewhere before deletion
```

---

## File Size Formatting

**Human-Readable Sizes**:

```python
def format_size(bytes):
    if bytes < 1024:
        return f"{bytes} B"
    elif bytes < 1024**2:
        return f"{bytes/1024:.1f} KB"
    elif bytes < 1024**3:
        return f"{bytes/1024**2:.1f} MB"
    else:
        return f"{bytes/1024**3:.1f} GB"
```

**Examples**:

- 500 bytes → "500 B"
- 2048 bytes → "2.0 KB"
- 5242880 bytes → "5.0 MB"

---

## Encoding Management

### Default Encoding Strategy

1. **Attempt UTF-8** (modern standard)
2. **Check for BOM** (Byte Order Mark)
3. **Try latin-1** (fallback for legacy files)
4. **Report encoding issues** clearly

### Encoding Detection

```python
# Simple BOM detection
with open(path, 'rb') as f:
    bom = f.read(4)
    if bom.startswith(b'\xef\xbb\xbf'):
        encoding = 'utf-8-sig'
    elif bom.startswith(b'\xff\xfe'):
        encoding = 'utf-16-le'
    # ... etc
```

---

## Best Practices

1. **Always Validate**: Check paths before operations
2. **Use Absolute Paths**: Clearer than relative paths
3. **Create Parent Dirs**: Auto-create for write operations
4. **Warn on Large Files**: Alert before reading > 10MB
5. **Human-Readable Sizes**: Format in KB/MB/GB
6. **UTF-8 Default**: Use UTF-8 unless specific encoding needed
7. **Clear Error Messages**: Explain what went wrong and how to fix
8. **Note Destructive Ops**: Warn before deletes

---

## Advanced Examples

### Example: Search and List

**Request**: "Find all .py files in project directory"

**Execution**:

```
Operation: search_files
Path: C:\Users\User\project
Pattern: *.py

✅ Found 8 Python files:

C:\Users\User\project\
- main.py (3.2 KB)
- utils.py (1.8 KB)
- config.py (0.5 KB)

C:\Users\User\project\modules\
- parser.py (5.1 KB)
- handler.py (4.3 KB)

C:\Users\User\project\tests\
- test_main.py (2.1 KB)
- test_utils.py (1.9 KB)
- conftest.py (0.3 KB)

Total: 19.2 KB across 8 files
```

---

### Example: Move with Validation

**Request**: "Move data.json from downloads to project folder"

**Execution**:

```
Operation: move_file
Source: C:\Users\User\Downloads\data.json
Destination: C:\Users\User\project\data.json

Validation:
✅ Source file exists (Size: 1.2 MB)
✅ Source is readable
✅ Destination directory exists
✅ Destination is writable

Executing move...

✅ File moved successfully

New location: C:\Users\User\project\data.json
```

---

## Troubleshooting

**Q: "File too large" warnings**
**A**: Use specialized tools (pandas for CSV, chunk readers) or process in parts

**Q: "Permission denied" errors**
**A**: Check file/folder permissions, run as admin if needed, or choose different location

**Q: "Encoding errors" when reading**
**A**: Try different encodings (latin-1, windows-1252), use encoding detection

**Q: Can't delete directory**
**A**: Ensure directory is empty first, or use recursive delete if available
