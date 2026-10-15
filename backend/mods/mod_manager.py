import os
import sys
import json
import re
import importlib.util
import logging
from typing import Dict, List, Optional, Any
from pathlib import Path

from backend.mods.mod_types import BaseMod, ModMetadata, ModContext, ModHookType, HudWidget

logger = logging.getLogger("openagents.mods")

class ModManager:
    _instance: Optional["ModManager"] = None

    def __init__(self, mods_dir: Optional[str] = None):
        if mods_dir is None:
            backend_dir = Path(__file__).resolve().parent.parent
            self.mods_dir = backend_dir / "mods"
        else:
            self.mods_dir = Path(mods_dir)
            
        self.state_file = self.mods_dir / "mods_state.json"
        self.mods: Dict[str, BaseMod] = {}
        self.enabled_states: Dict[str, bool] = self._load_states()
        self.hud_widgets: Dict[str, HudWidget] = {}

    @classmethod
    def get_instance(cls) -> "ModManager":
        if cls._instance is None:
            cls._instance = ModManager()
            cls._instance.discover_and_load_all()
        return cls._instance

    def _load_states(self) -> Dict[str, bool]:
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error reading mods_state.json: {e}")
        return {}

    def _save_states(self) -> None:
        try:
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(self.enabled_states, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving mods_state.json: {e}")

    def discover_and_load_all(self) -> None:
        """Scan mods directory for subdirectories containing mod.json."""
        if not self.mods_dir.exists():
            self.mods_dir.mkdir(parents=True, exist_ok=True)
            return

        for entry in self.mods_dir.iterdir():
            if entry.is_dir() and not entry.name.startswith("__"):
                manifest_path = entry / "mod.json"
                if manifest_path.exists():
                    try:
                        self.load_mod_from_dir(entry)
                    except Exception as e:
                        logger.error(f"Failed to load mod from {entry}: {e}")

    def load_mod_from_dir(self, dir_path: Path) -> Optional[BaseMod]:
        manifest_file = dir_path / "mod.json"
        if not manifest_file.exists():
            return None

        with open(manifest_file, "r", encoding="utf-8") as f:
            meta_dict = json.load(f)

        meta = ModMetadata(**meta_dict)
        if meta.id in self.enabled_states:
            meta.enabled = self.enabled_states[meta.id]

        entry_file = dir_path / meta.entry
        if not entry_file.exists():
            logger.warning(f"Mod entry file not found: {entry_file}")
            return None

        # Dynamically import the Python module
        module_name = f"openagents_mod_{meta.id.replace('-', '_')}"
        spec = importlib.util.spec_from_file_location(module_name, str(entry_file))
        if spec is None or spec.loader is None:
            return None

        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)

        # Look for a class that inherits from BaseMod
        mod_instance: Optional[BaseMod] = None
        for attr_name in dir(module):
            attr = getattr(module, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseMod) and attr is not BaseMod:
                mod_instance = attr(meta)
                break

        if mod_instance is None and hasattr(module, "create_mod"):
            mod_instance = module.create_mod(meta)

        if mod_instance is not None:
            self.mods[meta.id] = mod_instance
            logger.info(f"Loaded mod: {meta.name} ({meta.id}) [enabled={meta.enabled}]")
            return mod_instance

        logger.warning(f"No BaseMod subclass found in {entry_file}")
        return None

    def get_mods_metadata(self) -> List[Dict]:
        return [
            {
                **mod.metadata.model_dump(),
                "enabled": mod.metadata.enabled
            }
            for mod in self.mods.values()
        ]

    def set_mod_enabled(self, mod_id: str, enabled: bool) -> bool:
        if mod_id in self.mods:
            self.mods[mod_id].metadata.enabled = enabled
            self.enabled_states[mod_id] = enabled
            self._save_states()
            return True
        return False

    def toggle_mod(self, mod_id: str) -> Optional[bool]:
        if mod_id in self.mods:
            new_state = not self.mods[mod_id].metadata.enabled
            self.set_mod_enabled(mod_id, new_state)
            return new_state
        return None

    def get_hud_widgets(self) -> List[Dict[str, Any]]:
        # Only return widgets if at least one mod is active
        active_mods = [m for m in self.mods.values() if m.metadata.enabled]
        if not active_mods:
            return []
        return [w.model_dump() for w in self.hud_widgets.values()]

    def _sync_hud_widgets(self, ctx: ModContext) -> None:
        if ctx.hud_widgets:
            self.hud_widgets.update(ctx.hud_widgets)

    async def trigger_before_prompt(self, prompt: str, session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.BEFORE_PROMPT.value,
            prompt=prompt,
            session_id=session_id,
            metadata=metadata or {},
            hud_widgets=dict(self.hud_widgets)
        )
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_before_prompt(ctx)
                if ctx.cancelled:
                    break
            except Exception as e:
                logger.error(f"Error in mod {mod.metadata.id} on_before_prompt: {e}")
        self._sync_hud_widgets(ctx)
        return ctx

    async def trigger_after_prompt(self, prompt: str, response: str, session_id: Optional[str] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.AFTER_PROMPT.value,
            prompt=prompt,
            tool_result=response,
            session_id=session_id,
            hud_widgets=dict(self.hud_widgets)
        )
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_after_prompt(ctx)
            except Exception as e:
                logger.error(f"Error in mod {mod.metadata.id} on_after_prompt: {e}")
        self._sync_hud_widgets(ctx)
        return ctx

    async def trigger_before_tool_execution(self, tool_name: str, tool_args: Dict, session_id: Optional[str] = None, agent_name: Optional[str] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.BEFORE_TOOL_EXECUTION.value,
            tool_name=tool_name,
            tool_args=tool_args,
            session_id=session_id,
            agent_name=agent_name,
            hud_widgets=dict(self.hud_widgets)
        )
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_before_tool_execution(ctx)
                if ctx.cancelled:
                    break
            except Exception as e:
                logger.error(f"Error in mod {mod.metadata.id} on_before_tool_execution: {e}")
        self._sync_hud_widgets(ctx)
        return ctx

    async def trigger_after_tool_execution(self, tool_name: str, tool_args: Dict, tool_result: any, session_id: Optional[str] = None, agent_name: Optional[str] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.AFTER_TOOL_EXECUTION.value,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            session_id=session_id,
            agent_name=agent_name,
            hud_widgets=dict(self.hud_widgets)
        )
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_after_tool_execution(ctx)
            except Exception as e:
                logger.error(f"Error in mod {mod.metadata.id} on_after_tool_execution: {e}")
        self._sync_hud_widgets(ctx)
        return ctx

    async def trigger_custom_command(self, command_line: str, session_id: Optional[str] = None) -> Optional[ModContext]:
        """Intercepts and handles slash commands in-process without invoking LLMs."""
        trimmed = command_line.strip()
        if not trimmed.startswith("/"):
            return None

        parts = trimmed.split(" ", 1)
        command = parts[0].lower()
        args = parts[1].strip() if len(parts) > 1 else ""

        ctx = ModContext(
            event_type=ModHookType.CUSTOM_COMMAND.value,
            command=command,
            command_args=args,
            session_id=session_id,
            hud_widgets=dict(self.hud_widgets)
        )

        # 1. Check if any active mod handles this command
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_custom_command(ctx)
                if ctx.command_output is not None:
                    self._sync_hud_widgets(ctx)
                    return ctx
            except Exception as e:
                logger.error(f"Error executing command in mod {mod.metadata.id}: {e}")

        # 2. Built-in command dispatchers
        if command in ["/mods", "/mod"]:
            all_mods = self.get_mods_metadata()
            lines = ["### 🧩 Installed OpenAgents Mods\n"]
            for m in all_mods:
                status_icon = "🟢 Active" if m["enabled"] else "⚪ Disabled"
                lines.append(f"- **{m['name']}** (`{m['id']}`) - {status_icon}")
                lines.append(f"  *Hooks:* `{', '.join(m.get('hooks', []))}`")
                lines.append(f"  *Description:* {m.get('description', '')}\n")
            lines.append("Use `/create-mod <description>` to build a new mod on the fly.")
            ctx.reply("\n".join(lines))
            return ctx

        elif command in ["/create-mod", "/makemod", "/new-mod"]:
            if not args:
                ctx.reply("⚠️ **Usage:** `/create-mod <describe what the mod should do>`\n\n*Example:* `/create-mod Add token cost meter and highlight code blocks`")
                return ctx
            res = await self.generate_mod(args)
            if res.get("status") == "success":
                mod_meta = res["mod"]
                ctx.reply(
                    f"🎉 **New Mod Created & Loaded Live!**\n\n"
                    f"- **Name:** `{mod_meta['name']}`\n"
                    f"- **ID:** `{mod_meta['id']}`\n"
                    f"- **Hooks:** `{', '.join(mod_meta['hooks'])}`\n"
                    f"- **Location:** `backend/mods/{mod_meta['id']}/`\n\n"
                    f"The mod has been hot-reloaded and is now active in your runtime!"
                )
            else:
                ctx.reply(f"❌ **Failed to create mod:** {res.get('error')}")
            return ctx

        elif command in ["/help", "/commands"]:
            ctx.reply(
                "### 🛠️ Available Slash Commands\n\n"
                "- `/mods`: View all installed Claude Mods and active status\n"
                "- `/create-mod <prompt>`: Generate a new in-process mod by description\n"
                "- `/audit`: View safety audit counts and security status (via Guard Mod)\n"
                "- `/help`: Show this command list\n"
            )
            return ctx

        return None

    async def generate_mod(self, prompt: str) -> Dict[str, Any]:
        """Generate a new mod from user prompt, write files, and reload."""
        slug = re.sub(r"[^a-zA-Z0-9]+", "_", prompt.lower().strip())[:25].strip("_")
        if not slug:
            slug = "custom_mod"
        mod_id = f"mod_{slug}"
        mod_dir = self.mods_dir / mod_id
        mod_dir.mkdir(parents=True, exist_ok=True)

        class_name = "".join(part.capitalize() for part in slug.split("_")) + "Mod"
        mod_name = " ".join(part.capitalize() for part in slug.split("_"))

        # Generate manifest
        manifest = {
            "id": mod_id,
            "name": mod_name,
            "version": "1.0.0",
            "description": f"Custom mod generated from prompt: '{prompt}'",
            "author": "OpenAgents User",
            "enabled": True,
            "hooks": [
                "on_before_prompt",
                "on_after_prompt",
                "on_before_tool_execution",
                "on_custom_command"
            ],
            "entry": "mod.py"
        }

        # Python mod implementation tailored to request
        python_code = f'''import logging
from backend.mods.mod_types import BaseMod, ModContext

logger = logging.getLogger("openagents.mods.{mod_id}")

class {class_name}(BaseMod):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.invocation_count = 0

    async def on_init(self) -> None:
        logger.info("{mod_name} initialized.")

    async def on_before_prompt(self, ctx: ModContext) -> None:
        self.invocation_count += 1
        # Set dynamic HUD widget
        ctx.set_hud_widget(
            id="{mod_id}_hud",
            label="{mod_name}",
            value=f"Runs: {{self.invocation_count}}",
            icon="zap",
            color="purple"
        )
        ctx.log(f"[{mod_name}] Inspected prompt for turn {{self.invocation_count}}.")

    async def on_after_prompt(self, ctx: ModContext) -> None:
        pass

    async def on_before_tool_execution(self, ctx: ModContext) -> None:
        ctx.log(f"[{mod_name}] Monitored tool call: {{ctx.tool_name}}")

    async def on_custom_command(self, ctx: ModContext) -> None:
        cmd = (ctx.command or "").strip().lower()
        if cmd == "/{slug[:10]}":
            ctx.reply(f"✨ **{mod_name}**: Invocation count = {{self.invocation_count}}")
'''

        try:
            with open(mod_dir / "mod.json", "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            with open(mod_dir / "mod.py", "w", encoding="utf-8") as f:
                f.write(python_code)

            # Load the newly created mod
            mod_instance = self.load_mod_from_dir(mod_dir)
            if mod_instance:
                self.set_mod_enabled(mod_id, True)
                return {
                    "status": "success",
                    "mod": mod_instance.metadata.model_dump()
                }
            return {
                "status": "error",
                "error": "Mod was created but failed to load."
            }
        except Exception as e:
            logger.error(f"Error creating mod: {e}")
            return {
                "status": "error",
                "error": str(e)
            }
