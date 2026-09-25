import os
import shutil
import pathlib
from datetime import datetime
from typing import List, Union, Dict
import send2trash

from pydantic import BaseModel, Field
from langchain.tools import BaseTool

def format_size(size_bytes: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"

class ListDirectorySchema(BaseModel):
    paths: Union[str, List[str]] = Field(default=".", description="Directory path or list of directory paths to list.")

class ListDirectoryTool(BaseTool):
    name: str = "list_directory"
    description: str = "List the contents of one or more directories, displaying each item's name, type (file or directory), size, and last modified date."
    args_schema: type[BaseModel] = ListDirectorySchema

    def _run(self, paths: Union[str, List[str]] = ".") -> str:
        def format_directory_listing(path: str) -> str:
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

class ReadFileSchema(BaseModel):
    path: str = Field(..., description="File path to read.")
    encoding: str = Field(default="utf-8", description="Text encoding to use.")

class ReadFileTool(BaseTool):
    name: str = "read_file"
    description: str = "Read and return the contents of a text file at the specified path using the given encoding (default: UTF-8)."
    args_schema: type[BaseModel] = ReadFileSchema

    def _run(self, path: str, encoding: str = "utf-8") -> str:
        try:
            abs_path = os.path.abspath(path)
            if not os.path.exists(abs_path):
                return f"❌ File not found: {path}"
            if not os.path.isfile(abs_path):
                return f"❌ Not a file: {path}"

            size_bytes = os.path.getsize(abs_path)
            if size_bytes > 10 * 1024 * 1024:
                return f"⚠️ File too large ({format_size(size_bytes)}). Use a tool capable of chunked reading."

            with open(abs_path, 'r', encoding=encoding) as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            return f"❌ Encoding error: Could not read {path} with {encoding}. Try a different encoding."
        except Exception as e:
            return f"❌ Error reading file: {str(e)}"

class CreateBulkSchema(BaseModel):
    files: List[Dict[str, str]] = Field(..., description="Items with 'path' and 'content' keys.")

class CreateBulkTool(BaseTool):
    name: str = "create_bulk"
    description: str = "Create multiple files at once, each with specified content."
    args_schema: type[BaseModel] = CreateBulkSchema

    def _run(self, files: List[Dict[str, str]]) -> str:
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

class MoveBulkSchema(BaseModel):
    moves: List[Dict[str, str]] = Field(..., description="Items with 'source' and 'destination' keys.")

class MoveBulkTool(BaseTool):
    name: str = "move_bulk"
    description: str = "Move or rename multiple files or directories in a single operation."
    args_schema: type[BaseModel] = MoveBulkSchema

    def _run(self, moves: List[Dict[str, str]]) -> str:
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

class RenameBulkSchema(BaseModel):
    renames: List[Dict[str, str]] = Field(..., description="Items with 'old_name' and 'new_name' keys.")

class RenameBulkTool(BaseTool):
    name: str = "rename_bulk"
    description: str = "Rename multiple files or directories in a single operation."
    args_schema: type[BaseModel] = RenameBulkSchema

    def _run(self, renames: List[Dict[str, str]]) -> str:
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

class CopyFileSchema(BaseModel):
    source: str = Field(..., description="Source file or directory path.")
    destination: str = Field(..., description="Destination path.")

class CopyFileTool(BaseTool):
    name: str = "copy_file_tool"
    description: str = "Copy a file or directory from the source path to the destination path."
    args_schema: type[BaseModel] = CopyFileSchema

    def _run(self, source: str, destination: str) -> str:
        try:
            if os.path.isdir(source):
                shutil.copytree(source, destination)
            else:
                shutil.copy2(source, destination)
            return f"✅ Successfully copied {source} to {destination}"
        except Exception as e:
            return f"❌ Error copying {source}: {str(e)}"

class DeleteBulkSchema(BaseModel):
    paths: List[str] = Field(..., description="File or directory paths to delete.")

class DeleteBulkTool(BaseTool):
    name: str = "delete_bulk"
    description: str = "Move multiple files or directories to the recycle bin (soft delete) in one operation."
    args_schema: type[BaseModel] = DeleteBulkSchema

    def _run(self, paths: List[str]) -> str:
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

class CreateDirectorySchema(BaseModel):
    path: str = Field(..., description="Directory path to create.")

class CreateDirectoryTool(BaseTool):
    name: str = "create_directory"
    description: str = "Create a new directory at the specified path, including any necessary parent directories."
    args_schema: type[BaseModel] = CreateDirectorySchema

    def _run(self, path: str) -> str:
        try:
            os.makedirs(path, exist_ok=True)
            return f"✅ Successfully created directory: {path}"
        except Exception as e:
            return f"❌ Error creating directory: {str(e)}"

class DeleteDirectorySchema(BaseModel):
    path: str = Field(..., description="Directory path to delete.")
    recursive: bool = Field(default=False, description="Unused; retained for compatibility.")

class DeleteDirectoryTool(BaseTool):
    name: str = "delete_directory"
    description: str = "Move a directory to the recycle bin (soft delete)."
    args_schema: type[BaseModel] = DeleteDirectorySchema

    def _run(self, path: str, recursive: bool = False) -> str:
        try:
            if not os.path.isdir(path):
                return f"❌ Not a directory: {path}"
            send2trash.send2trash(os.path.abspath(path))
            return f"✅ Successfully moved directory {path} to recycle bin"
        except Exception as e:
            return f"❌ Error deleting directory: {str(e)}"

class SearchFilesSchema(BaseModel):
    pattern: str = Field(..., description="Glob pattern to match.")
    path: str = Field(default=".", description="Root directory to search.")

class SearchFilesTool(BaseTool):
    name: str = "search_files"
    description: str = "Search for files matching a glob pattern within the specified directory and its subdirectories."
    args_schema: type[BaseModel] = SearchFilesSchema

    def _run(self, pattern: str, path: str = ".") -> str:
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

class WriteFileSchema(BaseModel):
    markdown_content: str = Field(..., description="Markdown text to convert/write.")
    output_formats: Union[str, List[str]] = Field(default="md", description="Target format or list of formats.")
    output_paths: Union[str, List[str], None] = Field(default=None, description="Target file path or list of paths.")

class WriteFileTool(BaseTool):
    name: str = "write-file"
    description: str = "Write markdown content to one or more output formats (docx, pdf, txt, etc.) and save to corresponding files."
    args_schema: type[BaseModel] = WriteFileSchema

    def _run(self, markdown_content: str, output_formats: Union[str, List[str]] = "md", output_paths: Union[str, List[str]] = None) -> str:
        import tempfile
        
        formats = [output_formats] if isinstance(output_formats, str) else output_formats
        supported_formats = ["docx", "pdf", "html", "txt", "md"]
        
        if output_paths is None:
            paths = [f"converted_output.{f if f in supported_formats else 'md'}" for f in formats]
        else:
            paths = [output_paths] if isinstance(output_paths, str) else output_paths

        if len(formats) != len(paths):
            return f"❌ Mismatch: Received {len(formats)} formats and {len(paths)} paths."

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

from langchain_core.tools import BaseToolkit

class FileSystemToolkit(BaseToolkit):
    def get_tools(self) -> List[BaseTool]:
        return [
            ListDirectoryTool(),
            ReadFileTool(),
            CreateBulkTool(),
            MoveBulkTool(),
            RenameBulkTool(),
            CopyFileTool(),
            DeleteBulkTool(),
            CreateDirectoryTool(),
            DeleteDirectoryTool(),
            SearchFilesTool(),
            WriteFileTool()
        ]
