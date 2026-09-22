import pytest
import pathlib
from backend.agents.file_system_agent import search_files_tool

def test_search_files_happy_path(mocker):
    # Mock pathlib.Path.rglob to return a list of fake PosixPath/WindowsPath objects
    mock_rglob = mocker.patch("pathlib.Path.rglob")
    mock_rglob.return_value = (pathlib.Path("fake/path/file1.txt"), pathlib.Path("fake/path/file2.txt"))

    result = search_files_tool.invoke({"pattern": "*.txt", "path": "fake/path"})

    assert "✅ Found 2 results:" in result
    assert f"- {pathlib.Path('fake/path/file1.txt')}" in result
    assert f"- {pathlib.Path('fake/path/file2.txt')}" in result

def test_search_files_no_files_found(mocker):
    mock_rglob = mocker.patch("pathlib.Path.rglob")
    mock_rglob.return_value = []

    result = search_files_tool.invoke({"pattern": "*.py", "path": "empty/dir"})

    assert result == "🔍 No files found matching '*.py' in empty/dir"

def test_search_files_exception(mocker):
    mock_rglob = mocker.patch("pathlib.Path.rglob")
    mock_rglob.side_effect = Exception("Mock error")

    result = search_files_tool.invoke({"pattern": "*", "path": "."})

    assert result == "❌ Error searching files: Mock error"
