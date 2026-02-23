"""
Agentic file system agent using LangChain's FileManagementToolkit and a real LLM.
This agent receives instructions and uses all available file system tools as needed.
"""
import sys
import os
import shutil
import pathlib
from datetime import datetime
from typing import List, Optional, Union

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from langchain.tools import tool
from langchain.agents import create_agent
from backend.agents.model_providers.agent_llms import agent_llms

# --- Markdown conversion tool imports ---
import pypandoc

model = agent_llms['FileSystemAgent']

def format_size(size_bytes: int) -> str:
    """Format bytes into human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

@tool("list_directory")
def list_directory_tool(path: str = ".") -> str:
    """
    List contents of a directory with size and type info.
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

        output = [f"✅ Contents of {path}:", "Directories:"]
        output.extend([f"  {d}" for d in sorted(dirs)])
        output.append("Files:")
        output.extend([f"  {f}" for f in sorted(files)])
        return "\n".join(output)
    except Exception as e:
        return f"❌ Error listing directory: {str(e)}"

@tool("read_file")
def read_file_tool(path: str, encoding: str = "utf-8") -> str:
    """
    Read contents of a text file.
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

@tool("write_file")
def write_file_tool(path: str, content: str, append: bool = False) -> str:
    """
    Create or update a file with the given content.
    """
    try:
        abs_path = os.path.abspath(path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        mode = 'a' if append else 'w'
        with open(abs_path, mode, encoding='utf-8') as f:
            f.write(content)
        return f"✅ Successfully {'appended to' if append else 'written to'} {path}"
    except Exception as e:
        return f"❌ Error writing file: {str(e)}"

@tool("move_file")
def move_file_tool(source: str, destination: str) -> str:
    """
    Move or rename a file or directory.
    """
    try:
        shutil.move(source, destination)
        return f"✅ Successfully moved {source} to {destination}"
    except Exception as e:
        return f"❌ Error moving {source}: {str(e)}"

@tool("copy_file_tool")
def copy_file_tool(source: str, destination: str) -> str:
    """
    Copy a file or directory.
    """
    try:
        if os.path.isdir(source):
            shutil.copytree(source, destination)
        else:
            shutil.copy2(source, destination)
        return f"✅ Successfully copied {source} to {destination}"
    except Exception as e:
        return f"❌ Error copying {source}: {str(e)}"

@tool("delete_file")
def delete_file_tool(path: str) -> str:
    """
    Permanently delete a file.
    """
    try:
        if os.path.isdir(path):
            return f"❌ {path} is a directory. Use delete_directory to remove it."
        os.remove(path)
        return f"✅ Successfully deleted {path}"
    except Exception as e:
        return f"❌ Error deleting file: {str(e)}"

@tool("create_directory")
def create_directory_tool(path: str) -> str:
    """
    Create a new directory.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return f"✅ Successfully created directory: {path}"
    except Exception as e:
        return f"❌ Error creating directory: {str(e)}"

@tool("delete_directory")
def delete_directory_tool(path: str, recursive: bool = False) -> str:
    """
    Remove a directory.
    """
    try:
        if not os.path.isdir(path):
            return f"❌ Not a directory: {path}"
        if recursive:
            shutil.rmtree(path)
        else:
            os.rmdir(path)
        return f"✅ Successfully deleted directory: {path}"
    except Exception as e:
        return f"❌ Error deleting directory: {str(e)}"

@tool("search_files")
def search_files_tool(pattern: str, path: str = ".") -> str:
    """
    Search for files matching a pattern using glob.
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

@tool("convert_markdown_content")
def convert_markdown_content_tool(markdown_content: str, output_format: str = "docx", output_path: str = None) -> str:
    """
    Convert markdown content to the specified format (docx, pdf, txt, etc.).
    Args:
        markdown_content: The markdown text to convert.
        output_format: Target format (docx, pdf, txt, etc.).
        output_path: Optional output file path. If not provided, uses 'converted_output.<ext>'.
    Returns:
        Success or error message with output file path.
    """
    import tempfile
    supported_formats = ["docx", "pdf", "txt", "markdown", "md"]
    if output_format not in supported_formats:
        return f"Unsupported output format: {output_format}. Supported: {', '.join(supported_formats)}."
    ext = output_format if output_format != "md" else "markdown"
    if output_path is None:
        output_path = f"converted_output.{ext}"
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".md", mode="w", encoding="utf-8") as tmp_md:
            tmp_md.write(markdown_content)
            tmp_md_path = tmp_md.name
        pypandoc.convert_file(tmp_md_path, output_format, outputfile=output_path)
        os.remove(tmp_md_path)
        return f"Conversion successful: {output_path}"
    except Exception as e:
        return f"Conversion failed: {str(e)}"

fs_tools = [
    list_directory_tool,
    read_file_tool,
    write_file_tool,
    move_file_tool,
    copy_file_tool,
    delete_file_tool,
    create_directory_tool,
    delete_directory_tool,
    search_files_tool,
    convert_markdown_content_tool
]

agent = create_agent(
    model,
    fs_tools,
    system_prompt=(
        "You are a File System Manager responsible for precise file and directory operations.",
        "",
        "CRITICAL DIRECTIVE: DO what is instructed and NEVER deviate from the given task. Complete the task efficiently without unnecessary questioning or alternative suggestions unless safety is compromised.",
        "",
        "AVAILABLE OPERATIONS:",
        "- list_directory: Enumerate directory contents with sizes and dates",
        "- read_file: Read text file contents (limit 10MB)",
        "- write_file: Create or overwrite files (auto-creates parent directories)",
        "- move_file: Rename or relocate files/directories",
        "- copy_file_tool: Duplicate files or repositories",
        "- delete_file: Permanently remove a file",
        "- create_directory: Initialize a new directory",
        "- delete_directory: Remove a folder (recursive option available)",
        "- search_files: Find files using patterns (e.g., *.py)",
        "- convert_markdown_content: Export markdown to docx, pdf, or txt",
        "",
        "EXECUTION STANDARDS:",
        "1. PATHS: Use absolute paths or reliable relative paths. Validate existence before processing.",
        "2. SAFETY: Avoid destructive operations unless explicitly requested. Warn about large file reads.",
        "3. CLEANLINESS: Automate parent directory creation. Default to UTF-8 encoding.",
        "4. FEEDBACK: Provide clear, structured success/error messages. Include sizes and counts where applicable.",
        "5. CONTEXT: Always process your content before performing file operations. Remove unnecessary context that the user doesn't intend, such as 'Previous Agent' or 'Previous agent response'.",
        "",
        "ERROR HANDLING:",
        "- If a file is missing, suggest potential alternatives if found in the same directory.",
        "- If permission is denied, clearly state it and suggest a different location.",
        "",
        "EXAMPLES:",
        "1. List files: action='list_directory', path='C:\\Projects\\App'",
        "2. Create log: action='write_file', path='logs/session.log', content='[INFO] System initialized'",
        "3. Remove temp: action='delete_file', path='temp/cache.tmp'",
        "4. Search code: action='search_files', pattern='*.py', path='.'",
        "",
        "Always use the provided manual tools. Do not rely on external toolkits or library-specific abstractions."
    ),
    name="FileSystemAgent"
)

def run_agentic_filesystem_demo():
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
