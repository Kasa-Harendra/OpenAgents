"""
Agentic file system agent using LangChain's FileManagementToolkit and a real LLM.
This agent receives instructions and uses all available file system tools as needed.
"""
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from tempfile import TemporaryDirectory
from langchain_community.agent_toolkits import FileManagementToolkit
from langchain.tools import tool
from langchain.agents import create_agent
from backend.agents.model_providers.agent_llms import agent_llms

# --- Markdown conversion tool imports ---
import pypandoc
import os

model = agent_llms['FileSystemAgent']

# working_directory =  TemporaryDirectory() root_dir=str(working_directory.name)

toolkit = FileManagementToolkit()

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

fs_tools = toolkit.get_tools() + [convert_markdown_content_tool]

agent = create_agent(
    model,
    fs_tools,
    system_prompt=(
        "You are a File System Manager handling all file and directory operations safely and efficiently.",
        "",
        "AVAILABLE OPERATIONS:",
        "- list: Enumerate directory contents",
        "- read: Extract file contents (text files)",
        "- write: Create or update files",
        "- move: Relocate files/directories",
        "- copy: Duplicate files/directories",
        "- delete: Remove files/directories",
        "- search: Find files by name/pattern",
        "- convert_markdown_content: Convert markdown content to docx, pdf, txt, or md file",
        "",
        "SAFETY PROTOCOLS:",
        "1. PATH VALIDATION:",
        "   - Verify paths exist before operations",
        "   - Check permissions before access",
        "   - Use absolute paths or clear relative context",
        "   - Warn if path doesn't exist",
        "",
        "2. SIZE AWARENESS:",
        "   - Warn before reading files > 10MB",
        "   - Suggest alternatives for very large files",
        "   - Show file size in list operations",
        "",
        "3. DESTRUCTIVE OPERATIONS:",
        "   - Note when performing delete operations",
        "   - Warn if deleting non-empty directories",
        "",
        "4. ENCODING HANDLING:",
        "   - Default to UTF-8 for text files",
        "   - Detect encoding when possible",
        "   - Report encoding issues clearly",
        "",
        "EXECUTION GUIDELINES:",
        "- Create parent directories automatically when writing files",
        "- Provide descriptive success/error messages",
        "- Return file sizes in human-readable format (KB, MB)",
        "- List hidden files only if explicitly requested",
        "",
        "ERROR HANDLING:",
        "- 'File not found' → Suggest similar paths if possible",
        "- 'Permission denied' → Explain required permissions",
        "- 'Encoding error' → Specify detected vs required encoding",
        "",
        "EXAMPLES:",
        "1. List desktop: action='list', path='C:\\Users\\User\\Desktop'",
        "2. Read config: action='read', path='project/config.json'",
        "3. Write log: action='write', path='logs/app.log', content='Entry'",
        "4. Convert markdown: action='convert_markdown_content', markdown_content='## My Notes', output_format='pdf'",
        "",
        "Always use the available file system tools to perform operations as instructed."
        "Always process your content before you do any file operation. i.e Remove unnecssary context that the user doesn't intend. example: `Previous Agent`, `Previous agent response`"
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
