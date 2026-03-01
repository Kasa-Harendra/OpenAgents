"""
Agentic file system agent using LangChain's FileManagementToolkit and a real LLM.
This agent receives instructions and uses all available file system tools as needed.
"""
import sys
import os
import shutil
import pathlib
from datetime import datetime
from typing import List, Optional, Union, Dict
import send2trash
from spire.doc import *
from spire.doc.common import *

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain.tools import tool
from langchain.agents import create_agent
from backend.agents.model_providers.agent_llms import get_agent_llm
from backend.agents.prompts import FILE_SYSTEM_PROMPT, get_structured_prompt

# --- Markdown conversion tool imports ---
import pypandoc

model = get_agent_llm('FileSystemAgent')

def format_size(size_bytes: int) -> str:
    """
    Format bytes into a human-readable string.
    Args:
        size_bytes (int): Number of bytes to format.
    Returns:
        str: Human-readable size string.
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@tool("list_directory")
def list_directory_tool(paths: Union[str, List[str]] = ".") -> str:
    """
    List the contents of one or more directories, displaying each item's name, type (file or directory), size, and last modified date.
    Returns a formatted summary per path or an error message if a path is invalid.
    Especially useful for inspecting multiple directories at once.
    Args:
        paths (Union[str, List[str]]): Directory path or list of directory paths to list.
    Returns:
        str: Formatted directory listings or error message.
    """
    def format_directory_listing(path: str) -> str:
        """
        Build a formatted listing for a single directory path.
        Args:
            path (str): Directory path to list.
        Returns:
            str: Formatted listing or error message.
        """
        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                return f"❌ Path does not exist: {path}"
            if not os.path.isdir(abs_path):
                return f"❌ Not a directory: {path}"

            items = os.listdir(abs_path)
            if not items:
                return f"✅ Directory is empty: {path}"

            dirs = []
            files = []
            for item in items:
                item_path = os.path.join(abs_path, item)
                try:
                    stats = os.stat(item_path)
                    size = format_size(stats.st_size)
                    mtime = datetime.fromtimestamp(stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                    if os.path.isdir(item_path):
                        dirs.append(f"📁 {item}/")
                    else:
                        files.append(f"📄 {item} ({size}, {mtime})")
                except Exception:
                    dirs.append(f"❓ {item} (error reading stats)")

            output = [f"✅ Contents of {path}:", f"Directories ({len(dirs)}):"]
            if dirs:
                output.extend([f"  {d}" for d in sorted(dirs)])
            else:
                output.append("  (none)")
            output.append(f"Files ({len(files)}):")
            if files:
                output.extend([f"  {f}" for f in sorted(files)])
            else:
                output.append("  (none)")
            return "\n".join(output)
        except Exception as e:
            return f"❌ Error listing directory: {str(e)}"

    if isinstance(paths, str):
        path_list = [paths]
    else:
        path_list = list(paths) if paths else []

    if not path_list:
        return "❌ No paths provided."

    sections = [format_directory_listing(path) for path in path_list]
    return "\n\n".join(sections)

@tool("read_file")
def read_file_tool(path: str, encoding: str = "utf-8") -> str:
    """
    Read and return the contents of a text file at the specified path using the given encoding (default: UTF-8).
    Returns an error message if the file is not found, is not a file, or is too large (>10MB).
    Suitable for reading single files, but can be used repeatedly for multiple files.
    Args:
        path (str): File path to read.
        encoding (str): Text encoding to use.
    Returns:
        str: File contents or error message.
    """
    try:
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"❌ File not found: {path}"
        if not os.path.isfile(abs_path):
            return f"❌ Not a file: {path}"

        size_bytes = os.path.getsize(abs_path)
        if size_bytes > 10 * 1024 * 1024: # 10MB limit
            return f"⚠️ File too large ({format_size(size_bytes)}). Use a tool capable of chunked reading."

        with open(abs_path, 'r', encoding=encoding) as f:
            content = f.read()
        return content
    except UnicodeDecodeError:
        return f"❌ Encoding error: Could not read {path} with {encoding}. Try a different encoding."
    except Exception as e:
        return f"❌ Error reading file: {str(e)}"

@tool("create_bulk")
def create_bulk_tool(files: List[Dict[str, str]]) -> str:
    """
    Create multiple files at once, each with specified content.
    Intended for use when creating more than two files in a single operation.
    Especially efficient for batch file creation tasks.
    Args:
        files (List[Dict[str, str]]): Items with 'path' and 'content' keys.
    Returns a summary of successes and failures for each file.
    """
    results = []
    for f in files:
        path = f.get('path')
        content = f.get('content')
        try:
            abs_path = os.path.abspath(path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(content)
            results.append(f"✅ Created {path}")
        except Exception as e:
            results.append(f"❌ Failed to create {path}: {str(e)}")
    return "\n".join(results)


@tool("move_bulk")
def move_bulk_tool(moves: List[Dict[str, str]]) -> str:
    """
    Move or rename multiple files or directories in a single operation.
    Intended for use when moving or renaming more than two files or directories at once.
    Especially efficient for batch move or rename operations.
    Args:
        moves (List[Dict[str, str]]): Items with 'source' and 'destination' keys.
    Returns a summary of successes and failures for each move.
    """
    results = []
    for move in moves:
        src = move.get('source')
        dst = move.get('destination')
        try:
            shutil.move(src, dst)
            results.append(f"✅ Moved {src} to {dst}")
        except Exception as e:
            results.append(f"❌ Failed to move {src} to {dst}: {str(e)}")
    return "\n".join(results)

@tool("rename_bulk")
def rename_bulk_tool(renames: List[Dict[str, str]]) -> str:
    """
    Rename multiple files or directories in a single operation.
    Intended for use when renaming more than two files or directories at once.
    Especially efficient for batch rename operations.
    Args:
        renames (List[Dict[str, str]]): Items with 'old_name' and 'new_name' keys.
    Returns a summary of successes and failures for each rename.
    """
    results = []
    for r in renames:
        old = r.get('old_name')
        new = r.get('new_name')
        try:
            os.rename(old, new)
            results.append(f"✅ Renamed {old} to {new}")
        except Exception as e:
            results.append(f"❌ Failed to rename {old} to {new}: {str(e)}")
    return "\n".join(results)

@tool("copy_file_tool")
def copy_file_tool(source: str, destination: str) -> str:
    """
    Copy a file or directory from the source path to the destination path.
    Supports both files and directories. Returns a success or error message.
    Best for single copy operations; for more than two, use a bulk approach.
    Args:
        source (str): Source file or directory path.
        destination (str): Destination path.
    Returns:
        str: Success or error message.
    """
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return f"✅ Successfully copied {source} to {destination}"
    except Exception as e:
        return f"❌ Error copying {source}: {str(e)}"

@tool("delete_bulk")
def delete_bulk_tool(paths: List[str]) -> str:
    """
    Move multiple files or directories to the recycle bin (soft delete) in one operation.
    Intended for use when deleting more than two files or directories at once.
    Especially efficient for batch delete operations.
    Args:
        paths (List[str]): File or directory paths to delete.
    Returns a summary of successes and failures for each path.
    """
    results = []
    for path in paths:
        try:
            if os.path.exists(path):
                send2trash.send2trash(os.path.abspath(path))
                results.append(f"✅ Moved {path} to recycle bin")
            else:
                results.append(f"❌ Path not found: {path}")
        except Exception as e:
            results.append(f"❌ Failed to delete {path}: {str(e)}")
    return "\n".join(results)

@tool("create_directory")
def create_directory_tool(path: str) -> str:
    """
    Create a new directory at the specified path, including any necessary parent directories.
    Returns a success or error message.
    Suitable for single directory creation; for more than two, use a loop or bulk method.
    Args:
        path (str): Directory path to create.
    Returns:
        str: Success or error message.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Successfully created directory: {path}"
    except Exception as e:
        return f"❌ Error creating directory: {str(e)}"

@tool("delete_directory")
def delete_directory_tool(path: str, recursive: bool = False) -> str:
    """
    Move a directory to the recycle bin (soft delete).
    Returns a success message or an error if the path is not a directory.
    Best for single directory deletions; for more than two, use the bulk tool.
    Args:
        path (str): Directory path to delete.
        recursive (bool): Unused; retained for compatibility.
    Returns:
        str: Success or error message.
    """
    try:
        if not os.path.isdir(path):
            return f"❌ Not a directory: {path}"
        send2trash.send2trash(os.path.abspath(path))
        return f"✅ Successfully moved directory {path} to recycle bin"
    except Exception as e:
        return f"❌ Error deleting directory: {str(e)}"

@tool("search_files")
def search_files_tool(pattern: str, path: str = ".") -> str:
    """
    Search for files matching a glob pattern within the specified directory and its subdirectories.
    Returns a formatted list of found files or a message if none are found.
    Especially useful for finding more than two files matching a pattern.
    Args:
        pattern (str): Glob pattern to match.
        path (str): Root directory to search.
    Returns:
        str: Search results or error message.
    """
    try:
        found = list(pathlib.Path(path).rglob(pattern))
        if not found:
            return f"🔍 No files found matching '{pattern}' in {path}"
        results = [f"✅ Found {len(found)} results:"]
        for f in found:
            results.append(f"- {f}")
        return "\n".join(results)
    except Exception as e:
        return f"❌ Error searching files: {str(e)}"

# --- Markdown conversion tool definition ---

@tool("write-file")
def write_file_tool(markdown_content: str, output_formats: Union[str, List[str]] = "md", output_paths: Union[str, List[str]] = None) -> str:
    """
    Write markdown content to one or more output formats (docx, pdf, txt, etc.) and save to corresponding files.
    Uses pypandoc as primary, with fallbacks for docx, pdf, and txt.
    Args:
        markdown_content (str): Markdown text to convert/write.
        output_formats (Union[str, List[str]]): Target format or list of formats.
        output_paths (Union[str, List[str]]): Target file path or list of paths.
                      If lists are provided, they must be the same length.
                      If only formats are provided, default filenames like 'converted_output.<ext>' are used.
    Returns:
        str: Summary of creation results.
    """
    import tempfile
    
    # Normalize inputs to lists
    formats = [output_formats] if isinstance(output_formats, str) else output_formats
    if output_paths is None:
        paths = [f"converted_output.{f if f != 'md' else 'markdown'}" for f in formats]
    else:
        paths = [output_paths] if isinstance(output_paths, str) else output_paths

    if len(formats) != len(paths):
        return f"❌ Mismatch: Received {len(formats)} formats and {len(paths)} paths."

    supported_formats = ["docx", "pdf", "html", "txt", "markdown", "md"]
    results = []

    def ensure_output_dir(path):
        try:
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        except Exception:
            pass

    for fmt, path in zip(formats, paths):
        if fmt not in supported_formats:
            results.append(f"❌ Unsupported format '{fmt}' for {path}")
            continue
        
        ensure_output_dir(path)
        
        success = False
        # Try pypandoc first
        try:
            import pypandoc
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w", encoding="utf-8") as tmp_md:
                tmp_md.write(markdown_content)
                tmp_md_path = tmp_md.name
            try:
                pypandoc.convert_file(tmp_md_path, fmt, outputfile=path, extra_args=["--standalone"])
                os.remove(tmp_md_path)
                results.append(f"✅ Creation successful: {path}")
                success = True
            except Exception:
                os.remove(tmp_md_path)
        except Exception:
            pass

        if success:
            continue

        # Fallbacks
        try:
            if fmt == "pdf":
                from markdown_pdf import MarkdownPdf, Section
                pdf = MarkdownPdf()
                content = markdown_content.strip()
                if content.startswith("##"):
                    content = content[1:]
                elif not content.startswith("#"):
                    content = "# \n" + content
                pdf.add_section(Section(content))
                pdf.save(path)
                results.append(f"✅ Conversion successful (fallback): {path}")
            elif fmt == "txt":
                import markdown2
                from bs4 import BeautifulSoup
                html = markdown2.markdown(markdown_content)
                soup = BeautifulSoup(html, "html.parser")
                text = soup.get_text()
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                results.append(f"✅ Conversion successful (fallback): {path}")
            elif fmt in ["md", "markdown"]:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(markdown_content)
                results.append(f"✅ Creation successful: {path}")
            else:
                results.append(f"❌ Conversion failed for {fmt} at {path}: No available fallback.")
        except Exception as e:
            results.append(f"❌ Conversion failed for {fmt} at {path}: {str(e)}")

    return "\n".join(results)

tools = [
    list_directory_tool,
    read_file_tool,
    create_bulk_tool,
    move_bulk_tool,
    rename_bulk_tool,
    copy_file_tool,
    delete_bulk_tool,
    create_directory_tool,
    delete_directory_tool,
    search_files_tool,
    write_file_tool
]

# Use centralized prompt helper for caching
structured_system_prompt = get_structured_prompt(model, FILE_SYSTEM_PROMPT)

agent = create_agent(
    model,
    tools,
    system_prompt=structured_system_prompt,
    name="FileSystemAgent"
)

def run_agentic_filesystem_demo():
    """
    Run a scripted demo of the file system agent.
    Returns:
        None
    """
    instructions = [
        ("user", "Write 'Hello World!' to a file named example.txt."),
        ("user", "List all files in the directory."),
        ("user", "Read the contents of example.txt."),
        ("user", "Move example.txt to example2.txt."),
        ("user", "Copy example2.txt to example3.txt."),
        ("user", "Search for all .txt files."),
        ("user", "Delete example2.txt."),
        ("user", "List all files in the directory again."),
    ]
    events = agent.stream({"messages": instructions}, stream_mode="values")
    for event in events:
        event["messages"][-1].pretty_print()

if __name__ == "__main__":
    run_agentic_filesystem_demo()
