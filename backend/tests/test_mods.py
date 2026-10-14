import unittest
import asyncio
from fastapi.testclient import TestClient
from backend.main import app
from backend.mods.mod_manager import ModManager

class TestClaudeMods(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.mgr = ModManager.get_instance()
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

    async def test_guard_mod_before_prompt(self):
        prompt = "Please analyze this token: sk-ant-1234567890abcdef12345678 and tell me what it is."
        ctx = await self.mgr.trigger_before_prompt(prompt)
        self.assertIn("[REDACTED_API_TOKEN]", ctx.prompt)
        self.assertNotIn("sk-ant-1234567890abcdef12345678", ctx.prompt)
        self.assertGreater(len(ctx.logs), 0)

    async def test_guard_mod_tool_guardrail(self):
        # Safe tool call
        safe_ctx = await self.mgr.trigger_before_tool_execution("TerminalAgent", {"commands": ["ls -la"]})
        self.assertFalse(safe_ctx.cancelled)

        # Dangerous tool call
        dangerous_ctx = await self.mgr.trigger_before_tool_execution("TerminalAgent", {"commands": ["rm -rf /"]})
        self.assertTrue(dangerous_ctx.cancelled)
        self.assertIn("Blocked high-risk command", dangerous_ctx.cancel_reason)

    async def test_guard_mod_after_tool(self):
        raw_output = "Command output leaked secret: sk-ant-secretkey999999999999"
        ctx = await self.mgr.trigger_after_tool_execution("TerminalAgent", {}, raw_output)
        self.assertIn("[REDACTED_OUTPUT_TOKEN]", ctx.tool_result)
        self.assertNotIn("sk-ant-secretkey999999999999", ctx.tool_result)

if __name__ == "__main__":
    unittest.main()
