import unittest
import asyncio
import shutil
from fastapi.testclient import TestClient
from backend.main import app
from backend.mods.mod_manager import ModManager

class TestClaudeMods(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mgr = ModManager.get_instance()
        self.mgr.discover_and_load_all()
        self.mgr.set_mod_enabled("openagents-guard-sample", True)

    def test_mods_api_endpoints(self):
        # 1. List mods
        res = self.client.get("/mods")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertGreaterEqual(len(data), 1)
        mod = next((m for m in data if m["id"] == "openagents-guard-sample"), None)
        self.assertIsNotNone(mod)
        self.assertEqual(mod["name"], "Guard & Auditor Mod")
        self.assertIn("on_before_prompt", mod["hooks"])

        # 2. Get active mods
        active_res = self.client.get("/mods/active")
        self.assertEqual(active_res.status_code, 200)
        active_data = active_res.json()
        self.assertGreaterEqual(active_data["total_installed"], 1)
        self.assertGreaterEqual(active_data["total_active"], 1)

        # 3. Toggle mod state
        toggle_res = self.client.post("/mods/openagents-guard-sample/toggle")
        self.assertEqual(toggle_res.status_code, 200)
        self.assertEqual(toggle_res.json()["mod_id"], "openagents-guard-sample")

        # Toggle back to enabled
        toggle_res2 = self.client.post("/mods/openagents-guard-sample/toggle")
        self.assertEqual(toggle_res2.status_code, 200)
        self.assertTrue(toggle_res2.json()["enabled"])

    async def test_guard_mod_before_prompt_and_hud(self):
        prompt = "Please analyze this token: sk-ant-1234567890abcdef12345678 and tell me what it is."
        ctx = await self.mgr.trigger_before_prompt(prompt)
        self.assertIn("[REDACTED_API_TOKEN]", ctx.prompt)
        self.assertNotIn("sk-ant-1234567890abcdef12345678", ctx.prompt)
        self.assertGreater(len(ctx.logs), 0)
        
        # Verify HUD widget was emitted
        hud_widgets = self.mgr.get_hud_widgets()
        self.assertGreaterEqual(len(hud_widgets), 1)
        guard_widget = next((w for w in hud_widgets if "guard" in w["id"]), None)
        self.assertIsNotNone(guard_widget)

    async def test_slash_commands(self):
        # Test /mods command
        ctx_mods = await self.mgr.trigger_custom_command("/mods")
        self.assertIsNotNone(ctx_mods)
        self.assertIn("Installed OpenAgents Mods", ctx_mods.command_output)

        # Test /audit command handled by Guard Mod
        ctx_audit = await self.mgr.trigger_custom_command("/audit")
        self.assertIsNotNone(ctx_audit)
        self.assertIn("Guard & Auditor Mod Status", ctx_audit.command_output)

        # Test /help command
        ctx_help = await self.mgr.trigger_custom_command("/help")
        self.assertIsNotNone(ctx_help)
        self.assertIn("Available Slash Commands", ctx_help.command_output)

    async def test_prompt_to_mod_generator(self):
        res = await self.mgr.generate_mod("Track test token usage and alert")
        self.assertEqual(res.get("status"), "success")
        mod_meta = res.get("mod")
        self.assertIsNotNone(mod_meta)
        self.assertIn("mod_", mod_meta["id"])
        
        # Verify the generated mod is loaded in the manager
        self.assertIn(mod_meta["id"], self.mgr.mods)

        # Cleanup generated test mod
        mod_dir = self.mgr.mods_dir / mod_meta["id"]
        if mod_dir.exists():
            shutil.rmtree(mod_dir)
        if mod_meta["id"] in self.mgr.mods:
            del self.mgr.mods[mod_meta["id"]]

if __name__ == "__main__":
    unittest.main()
