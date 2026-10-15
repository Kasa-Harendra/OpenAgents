import os
import tempfile
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

# Use a temporary directory for OPENAGENTS_HOME during testing
class TestOpenAgentsHome(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.test_home = Path(cls.temp_dir.name) / ".openagents"
        os.environ["OPENAGENTS_HOME"] = str(cls.test_home)

        # Import modules after setting env var
        import backend.config.openagents_dir as oad
        oad.OPENAGENTS_DIR = cls.test_home
        oad.CREDENTIALS_DIR = cls.test_home / "credentials"
        oad.SKILLS_DIR = cls.test_home / "skills"
        oad.MODS_DIR = cls.test_home / "mods"
        oad.HISTORY_DIR = cls.test_home / "history"
        oad.AUDIT_DIR = cls.test_home / "audit"
        oad.CONFIG_FILE = cls.test_home / "config.json"
        oad.DB_FILE = cls.test_home / "openagents.db"

        oad.ensure_openagents_dirs()

        from backend.main import app
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.temp_dir.cleanup()

    def test_directory_structure_created(self):
        self.assertTrue(self.test_home.exists())
        self.assertTrue((self.test_home / "credentials").is_dir())
        self.assertTrue((self.test_home / "skills").is_dir())
        self.assertTrue((self.test_home / "mods").is_dir())
        self.assertTrue((self.test_home / "history").is_dir())
        self.assertTrue((self.test_home / "audit").is_dir())
        self.assertTrue((self.test_home / "config.json").is_file())

    def test_config_service(self):
        from backend.config.openagents_dir import load_config, update_config
        cfg = load_config()
        self.assertEqual(cfg["version"], "1.0.0")
        self.assertTrue(cfg["features"]["claude_mods"])

        update_config({"theme": "synthwave"})
        updated = load_config()
        self.assertEqual(updated["theme"], "synthwave")

    def test_skills_service_and_api(self):
        from backend.services.skills_service import SkillsService

        # 1. Create a custom skill in ~/.openagents/skills
        saved = SkillsService.save_skill(
            skill_id="docker-deploy",
            content="# Docker Deployment Guide\nUse docker compose up -d.",
            metadata={"name": "Docker Deployer", "description": "Automates containerized rollouts"}
        )
        self.assertEqual(saved["name"], "Docker Deployer")

        # 2. List skills
        skills = SkillsService.list_skills()
        skill_ids = [s["id"] for s in skills]
        self.assertIn("docker-deploy", skill_ids)

        # 3. Retrieve skill details
        detail = SkillsService.get_skill("docker-deploy")
        self.assertIsNotNone(detail)
        self.assertIn("docker compose", detail["instructions"])

        # 4. Prompt summary
        summary = SkillsService.get_skills_prompt_summary()
        self.assertIn("Docker Deployer", summary)

        # 5. REST API verification
        res = self.client.get("/skills")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(s["id"] == "docker-deploy" for s in res.json()))

    def test_history_service_and_api(self):
        from backend.services.history_service import HistoryService

        session_id = "test-session-12345"
        messages = [
            {"role": "user", "content": "Create a new react app", "timestamp": 1700000000},
            {"role": "assistant", "content": "App initialized.", "type": "agent_response", "timestamp": 1700000005}
        ]

        # 1. Save session
        saved = HistoryService.save_session(
            session_id=session_id,
            title="React Creation",
            messages=messages,
            base_directory="/tmp/workspace"
        )
        self.assertEqual(saved["title"], "React Creation")
        self.assertEqual(len(saved["messages"]), 2)

        # 2. Get session
        retrieved = HistoryService.get_session(session_id)
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved["id"], session_id)
        self.assertEqual(retrieved["base_directory"], "/tmp/workspace")

        # 3. List sessions
        sessions = HistoryService.list_sessions()
        self.assertTrue(any(s["id"] == session_id for s in sessions))

        # 4. REST API GET sessions
        res = self.client.get("/history/sessions")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(any(s["id"] == session_id for s in res.json()))

        # 5. REST API GET single session
        single_res = self.client.get(f"/history/sessions/{session_id}")
        self.assertEqual(single_res.status_code, 200)
        self.assertEqual(single_res.json()["title"], "React Creation")

        # 6. REST API DELETE session
        del_res = self.client.delete(f"/history/sessions/{session_id}")
        self.assertEqual(del_res.status_code, 200)
        self.assertIsNone(HistoryService.get_session(session_id))


if __name__ == "__main__":
    unittest.main()
