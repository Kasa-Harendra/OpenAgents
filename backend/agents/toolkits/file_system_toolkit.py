import os
import re
import glob
import shutil
import pathlib
from datetime import datetime
from typing import List, Union, Dict, Optional
import send2trash

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

# =====================================================================
# 1. Read File
# =====================================================================
class FileReadSchema(BaseModel):
    path: str = Field(..., description="Absolute or relative path to the file to read.")
    start_line: Optional[int] = Field(None, description="1-indexed starting line number (inclusive).")
    end_line: Optional[int] = Field(None, description="1-indexed ending line number (inclusive).")
    content_offset: Optional[int] = Field(0, description="Byte offset into the file for viewing truncated files.")

class FileReadTool(BaseTool):
    name: str = "file_read"
    description: str = (
        "Read a file's content with optional line slicing and byte pagination. "
        "Returns line-numbered output to make precise replacements easy. Max 800 lines or 45KB per read."
    )
    args_schema: type[BaseModel] = FileReadSchema

    def _run(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, content_offset: int = 0) -> str:
        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                return f"❌ File not found: {path}"
            if not os.path.isfile(abs_path):
                return f"❌ Not a regular file: {path}"

            with open(abs_path, 'r', encoding='utf-8', errors='replace') as f:
                if content_offset > 0:
                    f.seek(content_offset)
                raw_lines = f.readlines()

            total_lines = len(raw_lines)
            s_line = max(1, start_line) if start_line is not None else 1
            e_line = min(total_lines, end_line) if end_line is not None else min(total_lines, s_line + 799)

            if s_line > total_lines:
                return f"⚠️ Start line {s_line} is beyond total file lines ({total_lines})."

            selected_lines = raw_lines[s_line - 1 : e_line]
            formatted = []
            current_bytes = 0
            MAX_BYTES = 46080  # 45 KB

            truncated = False
            for idx, line in enumerate(selected_lines, start=s_line):
                line_str = f"{idx}: {line}"
                current_bytes += len(line_str.encode('utf-8'))
                if current_bytes > MAX_BYTES:
                    truncated = True
                    break
                formatted.append(line_str.rstrip('\r\n'))

            result_str = "\n".join(formatted)
            header = f"=== File: {path} (Lines {s_line} to {s_line + len(formatted) - 1} of {total_lines}) ===\n"
            if truncated:
                footer = f"\n\n⚠️ Output truncated at 45KB limit. Use start_line={s_line + len(formatted)} to read next chunk."
            else:
                footer = ""
            return header + result_str + footer
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"

# =====================================================================
# 2. Edit File
# =====================================================================
class FileEditSchema(BaseModel):
    target_file: str = Field(..., description="Path to the file to modify.")
    target_content: str = Field(..., description="The EXACT string to be replaced (must match character-by-character including indentation).")
    replacement_content: str = Field(..., description="The new replacement content to put in place of target_content.")
    start_line: Optional[int] = Field(None, description="Optional starting line to narrow search range.")
    end_line: Optional[int] = Field(None, description="Optional ending line to narrow search range.")

class FileEditTool(BaseTool):
    name: str = "file_edit"
    description: str = (
        "Make targeted, precise edits to an existing file by replacing an exact string match. "
        "Avoids rewriting the whole file, preserving existing comments and structure."
    )
    args_schema: type[BaseModel] = FileEditSchema

    def _run(self, target_file: str, target_content: str, replacement_content: str, start_line: Optional[int] = None, end_line: Optional[int] = None) -> str:
        try:
            abs_path = os.path.abspath(target_file)
            if not os.path.exists(abs_path):
                return f"❌ File not found: {target_file}"

            with open(abs_path, 'r', encoding='utf-8') as f:
                content = f.read()

            if start_line is not None or end_line is not None:
                lines = content.splitlines(keepends=True)
                s_idx = max(0, (start_line - 1) if start_line else 0)
                e_idx = min(len(lines), end_line if end_line else len(lines))
                
                before_block = "".join(lines[:s_idx])
                target_block = "".join(lines[s_idx:e_idx])
                after_block = "".join(lines[e_idx:])

                occurrences = target_block.count(target_content)
                if occurrences == 0:
                    return f"❌ Target content not found in lines {s_idx + 1} to {e_idx}."
                if occurrences > 1:
                    return f"❌ Target content occurs {occurrences} times in lines {s_idx + 1} to {e_idx}. Narrow down the line range."

                new_target_block = target_block.replace(target_content, replacement_content, 1)
                new_full_content = before_block + new_target_block + after_block
            else:
                occurrences = content.count(target_content)
                if occurrences == 0:
                    return "❌ Target content not found in file. Make sure whitespace and indentation match exactly."
                if occurrences > 1:
                    return f"❌ Target content occurs {occurrences} times in file. Provide start_line and end_line to disambiguate."

                new_full_content = content.replace(target_content, replacement_content, 1)

            # Write updated content
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(new_full_content)

            return f"✅ Successfully replaced target content in {target_file}."
        except Exception as e:
            return f"❌ Error editing file: {str(e)}"

# =====================================================================
# 3. Clean File Write / Create
# =====================================================================
class WriteFileSchema(BaseModel):
    path: str = Field(..., description="Destination file path.")
    content: str = Field(..., description="Complete text/code content to write.")
    overwrite: bool = Field(True, description="Whether to overwrite existing file.")

class WriteFileTool(BaseTool):
    name: str = "write_file"
    description: str = "Create a new file or completely overwrite an existing file with the provided content."
    args_schema: type[BaseModel] = WriteFileSchema

    def _run(self, path: str, content: str, overwrite: bool = True) -> str:
        try:
            abs_path = os.path.abspath(path)
            if os.path.exists(abs_path) and not overwrite:
                return f"❌ File already exists and overwrite is set to False: {path}"

            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return f"✅ Successfully wrote {len(content)} characters to {path}."
        except Exception as e:
            return f"❌ Error writing file: {str(e)}"

# =====================================================================
# 4. Fast Grep Code Search
# =====================================================================
class GrepSearchSchema(BaseModel):
    query: str = Field(..., description="Regex or literal search pattern.")
    path: str = Field(".", description="Root file or directory to search.")
    case_insensitive: bool = Field(True, description="Case-insensitive search.")
    file_pattern: Optional[str] = Field(None, description="Optional file glob filter, e.g. '*.py' or '*.ts'.")

class GrepSearchTool(BaseTool):
    name: str = "grep_search"
    description: str = "Search for a string or regex pattern across files in a directory. Returns matching line numbers and snippets."
    args_schema: type[BaseModel] = GrepSearchSchema

    def _run(self, query: str, path: str = ".", case_insensitive: bool = True, file_pattern: Optional[str] = None) -> str:
        try:
            abs_root = os.path.abspath(path)
            flags = re.IGNORECASE if case_insensitive else 0
            compiled_regex = re.compile(query, flags)
            
            matches = []
            MAX_MATCHES = 50

            # Single file search
            if os.path.isfile(abs_root):
                target_files = [abs_root]
            else:
                target_files = []
                for root, dirs, files in os.walk(abs_root):
                    # Skip noise directories
                    dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', '__pycache__', '.venv', 'dist', 'build']]
                    for f in files:
                        if file_pattern:
                            if pathlib.Path(f).match(file_pattern):
                                target_files.append(os.path.join(root, f))
                        else:
                            target_files.append(os.path.join(root, f))
                        if len(target_files) >= 500:
                            break

            for file_path in target_files:
                if len(matches) >= MAX_MATCHES:
                    break
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        for line_num, line in enumerate(f, start=1):
                            if compiled_regex.search(line):
                                rel_path = os.path.relpath(file_path, abs_root)
                                matches.append(f"{rel_path}:{line_num}: {line.strip()[:150]}")
                                if len(matches) >= MAX_MATCHES:
                                    break
                except Exception:
                    continue

            if not matches:
                return f"🔍 No matches found for pattern '{query}' in {path}."

            header = f"✅ Found {len(matches)} match(es):\n"
            return header + "\n".join(matches)
        except Exception as e:
            return f"❌ Error executing grep search: {str(e)}"

# =====================================================================
# 5. Glob Search Tool
# =====================================================================
class GlobSearchSchema(BaseModel):
    pattern: str = Field(..., description="Glob pattern, e.g. '**/*.py' or 'src/**/*.tsx'.")
    path: str = Field(".", description="Base directory to search.")

class GlobSearchTool(BaseTool):
    name: str = "glob_search"
    description: str = "Find files matching a glob pattern recursively across directory trees."
    args_schema: type[BaseModel] = GlobSearchSchema

    def _run(self, pattern: str, path: str = ".") -> str:
        try:
            abs_base = os.path.abspath(path)
            full_pattern = os.path.join(abs_base, pattern)
            found = glob.glob(full_pattern, recursive=True)
            
            # Filter noise
            filtered = [f for f in found if not any(p in f for p in ['.git', 'node_modules', '__pycache__'])]
            if not filtered:
                return f"🔍 No files found matching '{pattern}' in {path}."

            results = [f"✅ Found {len(filtered)} file(s):"]
            for f in filtered[:100]:
                results.append(f"- {os.path.relpath(f, abs_base)}")
            if len(filtered) > 100:
                results.append(f"...and {len(filtered) - 100} more files.")
            return "\n".join(results)
        except Exception as e:
            return f"❌ Error searching files: {str(e)}"

# =====================================================================
# 6. List Directory Tool
# =====================================================================
class ListDirectorySchema(BaseModel):
    paths: Union[str, List[str]] = Field(default=".", description="Directory path or list of paths to list.")

class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = "List directory contents showing names, sizes, and file types."
    args_schema: type[BaseModel] = ListDirectorySchema

    def _run(self, paths: Union[str, List[str]] = ".") -> str:
        path_list = [paths] if isinstance(paths, str) else paths
        results = []
        for p in path_list:
            try:
                abs_p = os.path.abspath(p)
                if not os.path.exists(abs_p):
                    results.append(f"❌ Path not found: {p}")
                    continue
                if not os.path.isdir(abs_p):
                    results.append(f"❌ Not a directory: {p}")
                    continue

                entries = os.listdir(abs_p)
                dirs = []
                files = []
                for item in sorted(entries):
                    if item in ['.git', '__pycache__']:
                        continue
                    item_path = os.path.join(abs_p, item)
                    if os.path.isdir(item_path):
                        dirs.append(f"📁 {item}/")
                    else:
                        size = format_size(os.path.getsize(item_path))
                        files.append(f"📄 {item} ({size})")

                out = [f"✅ Contents of {p}:", f"Directories ({len(dirs)}):"]
                out.extend([f"  {d}" for d in dirs] if dirs else ["  (none)"])
                out.append(f"Files ({len(files)}):")
                out.extend([f"  {f}" for f in files] if files else ["  (none)"])
                results.append("\n".join(out))
            except Exception as e:
                results.append(f"❌ Error listing {p}: {str(e)}")
        return "\n\n".join(results)

# =====================================================================
# 7. Helper Bulk & Directory Tools
# =====================================================================
class CreateDirectorySchema(BaseModel):
    path: str = Field(..., description="Directory path to create.")

class CreateDirectoryTool(BaseTool):
    name: str = "create_directory"
    description: str = "Create a directory, including all necessary parent directories."
    args_schema: type[BaseModel] = CreateDirectorySchema

    def _run(self, path: str) -> str:
        try:
            os.makedirs(path, exist_ok=True)
            return f"✅ Created directory: {path}"
        except Exception as e:
            return f"❌ Error creating directory: {str(e)}"

class DeleteBulkSchema(BaseModel):
    paths: List[str] = Field(..., description="List of file or directory paths to move to recycle bin.")

class DeleteBulkTool(BaseTool):
    name: str = "delete_bulk"
    description: str = "Safely move files or directories to the system recycle bin (soft delete)."
    args_schema: type[BaseModel] = DeleteBulkSchema

    def _run(self, paths: List[str]) -> str:
        results = []
        for path in paths:
            try:
                abs_p = os.path.abspath(path)
                if os.path.exists(abs_p):
                    send2trash.send2trash(abs_p)
                    results.append(f"✅ Moved {path} to recycle bin")
                else:
                    results.append(f"❌ Path not found: {path}")
            except Exception as e:
                results.append(f"❌ Failed to delete {path}: {str(e)}")
        return "\n".join(results)

# =====================================================================
# FileSystemToolkit Assembly
# =====================================================================
from langchain_core.tools import BaseToolkit

class FileSystemToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        return [
            FileReadTool(),
            FileEditTool(),
            WriteFileTool(),
            GrepSearchTool(),
            GlobSearchTool(),
            ListDirectoryTool(),
            CreateDirectoryTool(),
            DeleteBulkTool(),
        ]
