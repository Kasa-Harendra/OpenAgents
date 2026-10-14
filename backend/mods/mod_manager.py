import os
import sys
import json
import importlib.util
import logging
from typing import Dict, List, Optional
from pathlib import Path

from backend.mods.mod_types import BaseMod, ModMetadata, ModContext, ModHookType

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

    async def trigger_before_prompt(self, prompt: str, session_id: Optional[str] = None, metadata: Optional[Dict] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.BEFORE_PROMPT.value,
            prompt=prompt,
            session_id=session_id,
            metadata=metadata or {}
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
        return ctx

    async def trigger_after_prompt(self, prompt: str, response: str, session_id: Optional[str] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.AFTER_PROMPT.value,
            prompt=prompt,
            tool_result=response,
            session_id=session_id
        )
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_after_prompt(ctx)
            except Exception as e:
                logger.error(f"Error in mod {mod.metadata.id} on_after_prompt: {e}")
        return ctx

    async def trigger_before_tool_execution(self, tool_name: str, tool_args: Dict, session_id: Optional[str] = None, agent_name: Optional[str] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.BEFORE_TOOL_EXECUTION.value,
            tool_name=tool_name,
            tool_args=tool_args,
            session_id=session_id,
            agent_name=agent_name
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
        return ctx

    async def trigger_after_tool_execution(self, tool_name: str, tool_args: Dict, tool_result: any, session_id: Optional[str] = None, agent_name: Optional[str] = None) -> ModContext:
        ctx = ModContext(
            event_type=ModHookType.AFTER_TOOL_EXECUTION.value,
            tool_name=tool_name,
            tool_args=tool_args,
            tool_result=tool_result,
            session_id=session_id,
            agent_name=agent_name
        )
        for mod in self.mods.values():
            if not mod.metadata.enabled:
                continue
            try:
                await mod.on_after_tool_execution(ctx)
            except Exception as e:
                logger.error(f"Error in mod {mod.metadata.id} on_after_tool_execution: {e}")
        return ctx
