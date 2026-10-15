import re
from backend.mods.mod_types import BaseMod, ModContext

SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9_-]{20,}", re.IGNORECASE),
    re.compile(r"ghp_[a-zA-Z0-9]{20,}", re.IGNORECASE),
    re.compile(r"bearer\s+[a-zA-Z0-9\._-]{20,}", re.IGNORECASE),
]

DANGEROUS_COMMANDS = [
    "rm -rf /",
    ":(){ :|:& };:",
    "mkfs",
    "dd if=/dev/zero",
    "> /dev/sda",
]

class GuardAndAuditorMod(BaseMod):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.audited_ops = 0
        self.masked_secrets = 0

    async def on_init(self) -> None:
        pass

    async def on_before_prompt(self, ctx: ModContext) -> None:
        # Emit live HUD widgets to desktop UI
        ctx.set_hud_widget("guard_shield", label="Security Guard", value="Active", icon="shield", color="emerald")
        ctx.set_hud_widget("guard_audits", label="Audited Ops", value=str(self.audited_ops), icon="terminal", color="blue")

        if not ctx.prompt:
            return

        # Redact secrets before prompt reaches the LLM
        modified_prompt = ctx.prompt
        for pattern in SECRET_PATTERNS:
            if pattern.search(modified_prompt):
                modified_prompt = pattern.sub("[REDACTED_API_TOKEN]", modified_prompt)
                self.masked_secrets += 1
                ctx.log("GuardMod: Sensitive token in prompt was masked.")

        ctx.prompt = modified_prompt
        ctx.metadata["guard_mod_inspected"] = True
        ctx.metadata["masked_secrets"] = self.masked_secrets

    async def on_before_tool_execution(self, ctx: ModContext) -> None:
        self.audited_ops += 1
        ctx.set_hud_widget("guard_audits", label="Audited Ops", value=str(self.audited_ops), icon="terminal", color="blue")

        # Check command if TerminalAgent is executing
        if ctx.tool_args:
            command_str = str(ctx.tool_args).lower()
            for dangerous in DANGEROUS_COMMANDS:
                if dangerous in command_str:
                    ctx.abort(f"GuardMod: Blocked high-risk command execution: '{dangerous}'")
                    return

        ctx.log(f"GuardMod: Tool '{ctx.tool_name}' verified safe.")

    async def on_after_tool_execution(self, ctx: ModContext) -> None:
        # Redact secrets in tool outputs if string
        if isinstance(ctx.tool_result, str):
            modified_res = ctx.tool_result
            for pattern in SECRET_PATTERNS:
                if pattern.search(modified_res):
                    modified_res = pattern.sub("[REDACTED_OUTPUT_TOKEN]", modified_res)
                    self.masked_secrets += 1
                    ctx.log("GuardMod: Masked token found in tool output.")
            ctx.tool_result = modified_res

    async def on_custom_command(self, ctx: ModContext) -> None:
        cmd = (ctx.command or "").strip().lower()
        if cmd in ["/audit", "/guard"]:
            ctx.reply(
                f"🛡️ **Guard & Auditor Mod Status**\n\n"
                f"- **Protection State:** `Active & Monitoring`\n"
                f"- **Total Operations Audited:** `{self.audited_ops}`\n"
                f"- **Sensitive Tokens Masked:** `{self.masked_secrets}`\n"
                f"- **Restricted Commands:** `rm -rf /`, `mkfs`, `dd if=/dev/zero`, `:(){{ :|:& }};:`\n"
            )
