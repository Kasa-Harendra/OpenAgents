import os
import tempfile
import unittest
from pathlib import Path

from backend.agents.toolkits.file_system_toolkit import (
    FileReadTool,
    FileEditTool,
    WriteFileTool,
    GrepSearchTool,
    GlobSearchTool,
    ListDirectoryTool,
    FileSystemToolkit,
)
from backend.agents.toolkits.terminal_toolkit import (
    RunCommandTool,
    TerminalToolkit,
)
from backend.utils.context_compactor import compact_tool_output, compact_context


class TestClaudeTools(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_dir = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_write_file_and_read_file_tool(self):
        write_tool = WriteFileTool()
        read_tool = FileReadTool()

        test_file = self.test_dir / "subdir" / "sample.py"
        content = "line 1: import os\nline 2: import sys\nline 3: print('hello')\nline 4: print('world')\n"

        # 1. Write file with auto-creation of parent dir
        res = write_tool._run(path=str(test_file), content=content)
        self.assertIn("Successfully wrote", res)
        self.assertTrue(test_file.exists())

        # 2. Prevent accidental overwrite
        res_overwrite_fail = write_tool._run(path=str(test_file), content="new content", overwrite=False)
        self.assertIn("already exists", res_overwrite_fail)

        # 3. Allow overwrite
        res_overwrite_ok = write_tool._run(path=str(test_file), content=content, overwrite=True)
        self.assertIn("Successfully wrote", res_overwrite_ok)

        # 4. Read file with line slicing
        read_res = read_tool._run(path=str(test_file), start_line=2, end_line=3)
        self.assertIn("2: line 2: import sys", read_res)
        self.assertIn("3: line 3: print('hello')", read_res)
        self.assertNotIn("1: line 1", read_res)
        self.assertNotIn("4: line 4", read_res)

    def test_file_edit_tool(self):
        write_tool = WriteFileTool()
        edit_tool = FileEditTool()

        test_file = self.test_dir / "editable.txt"
        initial_content = "apple\nbanana\ncherry\ndate\nbanana\n"
        write_tool._run(path=str(test_file), content=initial_content)

        # 1. Edit unique target string
        res = edit_tool._run(
            target_file=str(test_file),
            target_content="cherry",
            replacement_content="blueberry"
        )
        self.assertIn("Successfully replaced target content", res)
        with open(test_file, "r") as f:
            updated = f.read()
        self.assertIn("blueberry", updated)
        self.assertNotIn("cherry", updated)

        # 2. Disambiguate multiple occurrences using line ranges
        res_ambiguous = edit_tool._run(
            target_file=str(test_file),
            target_content="banana",
            replacement_content="orange"
        )
        self.assertIn("occurs 2 times", res_ambiguous)

        # 3. Successful disambiguation with start_line and end_line
        res_sliced = edit_tool._run(
            target_file=str(test_file),
            target_content="banana",
            replacement_content="orange",
            start_line=1,
            end_line=3
        )
        self.assertIn("Successfully replaced target content", res_sliced)
        with open(test_file, "r") as f:
            lines = f.read().splitlines()
        self.assertEqual(lines[1], "orange")
        self.assertEqual(lines[4], "banana")

        # 4. Target content not found error handling
        res_not_found = edit_tool._run(
            target_file=str(test_file),
            target_content="nonexistent_word",
            replacement_content="replacement"
        )
        self.assertIn("not found in file", res_not_found)

    def test_grep_and_glob_search_tools(self):
        write_tool = WriteFileTool()
        grep_tool = GrepSearchTool()
        glob_tool = GlobSearchTool()

        f1 = self.test_dir / "src" / "alpha.py"
        f2 = self.test_dir / "src" / "beta.txt"
        f3 = self.test_dir / "docs" / "guide.md"

        write_tool._run(str(f1), "def calculate_alpha():\n    return 42\n")
        write_tool._run(str(f2), "Configuration:\nalpha_enabled = True\n")
        write_tool._run(str(f3), "# User Guide\nThis is the manual.\n")

        # 1. Glob search
        glob_res = glob_tool._run(pattern="**/*.py", path=str(self.test_dir))
        self.assertIn("alpha.py", glob_res)
        self.assertNotIn("guide.md", glob_res)

        # 2. Grep search literal
        grep_res = grep_tool._run(query="alpha", path=str(self.test_dir))
        self.assertIn("alpha.py", grep_res)
        self.assertIn("beta.txt", grep_res)
        self.assertNotIn("guide.md", grep_res)

        # 3. Grep search with includes
        grep_filtered = grep_tool._run(query="alpha", path=str(self.test_dir), file_pattern="*.py")
        self.assertIn("alpha.py", grep_filtered)
        self.assertNotIn("beta.txt", grep_filtered)

    def test_terminal_toolkit(self):
        toolkit = TerminalToolkit(working_dir=str(self.test_dir))
        tools = toolkit.get_tools()
        self.assertEqual(len(tools), 1)
        run_tool = tools[0]

        # 1. Verify initial cwd (canonical realpath)
        self.assertEqual(
            os.path.realpath(run_tool._current_cwd),
            os.path.realpath(str(self.test_dir))
        )

        # 2. Run simple safe command
        res_run = run_tool._run(command="echo 'Testing Terminal'")
        self.assertIn("Testing Terminal", res_run)
        self.assertIn("Exit Code: 0", res_run)

        # 3. Persistent directory tracking via cd
        sub = self.test_dir / "nested"
        sub.mkdir()
        run_tool._run(command=f"cd '{str(sub)}'")
        self.assertEqual(
            os.path.realpath(run_tool._current_cwd),
            os.path.realpath(str(sub))
        )

        # 4. Dangerous command guardrail
        res_danger = run_tool._run(command="rm -rf /")
        self.assertIn("BLOCKED", res_danger)

    def test_context_compactor(self):
        # 1. Short output remains unchanged
        short_text = "Standard output line 1\nStandard output line 2\n"
        self.assertEqual(compact_tool_output(short_text, max_chars=1000), short_text)

        # 2. Long output is compacted with head and tail retained
        long_lines = [f"Log trace line #{i}: diagnostic payload {i * 100}" for i in range(500)]
        long_text = "\n".join(long_lines)
        compacted = compact_tool_output(long_text, max_chars=500)

        self.assertLess(len(compacted), 1000)
        self.assertIn("Log trace line #0", compacted)
        self.assertIn("Log trace line #499", compacted)
        self.assertIn("intermediate output for context efficiency", compacted)


if __name__ == "__main__":
    unittest.main()
