import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
import yaml

from backend.config.openagents_dir import get_skills_dir


class SkillsService:
    @staticmethod
    def _parse_skill_file(skill_file: Path) -> Dict[str, Any]:
        """
        Parses a SKILL.md file, separating YAML frontmatter from markdown instructions.
        """
        content = skill_file.read_text(encoding="utf-8", errors="replace")
        meta = {
            "name": skill_file.parent.name,
            "description": "",
            "compatibility": "",
            "instructions": content,
            "path": str(skill_file.resolve()),
        }

        # Check for YAML frontmatter between --- and ---
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", content, re.DOTALL)
        if frontmatter_match:
            raw_yaml, body = frontmatter_match.groups()
            try:
                parsed_yaml = yaml.safe_load(raw_yaml)
                if isinstance(parsed_yaml, dict):
                    meta.update(parsed_yaml)
            except Exception:
                pass
            meta["instructions"] = body.strip()

        return meta

    @staticmethod
    def list_skills() -> List[Dict[str, Any]]:
        """
        Scans ~/.openagents/skills/ and returns a list of installed skills.
        """
        skills_dir = get_skills_dir()
        if not skills_dir.exists():
            return []

        skills = []
        for item in sorted(skills_dir.iterdir()):
            if item.is_dir() and not item.name.startswith("."):
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    try:
                        parsed = SkillsService._parse_skill_file(skill_md)
                        skills.append({
                            "id": item.name,
                            "name": parsed.get("name", item.name),
                            "description": parsed.get("description", ""),
                            "compatibility": parsed.get("compatibility", ""),
                            "path": str(skill_md),
                            "has_scripts": (item / "scripts").is_dir(),
                            "has_resources": (item / "resources").is_dir(),
                        })
                    except Exception as e:
                        skills.append({
                            "id": item.name,
                            "name": item.name,
                            "error": str(e)
                        })
        return skills

    @staticmethod
    def get_skill(skill_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves full details and instructions for a specific skill from ~/.openagents/skills/.
        """
        skills_dir = get_skills_dir()
        target_dir = skills_dir / skill_id
        skill_md = target_dir / "SKILL.md"
        if not skill_md.exists():
            return None

        return SkillsService._parse_skill_file(skill_md)

    @staticmethod
    def save_skill(skill_id: str, content: str, metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Creates or updates a skill in ~/.openagents/skills/<skill_id>/SKILL.md.
        """
        skills_dir = get_skills_dir()
        target_dir = skills_dir / skill_id
        target_dir.mkdir(parents=True, exist_ok=True)
        skill_md = target_dir / "SKILL.md"

        if metadata:
            frontmatter_str = yaml.dump(metadata, sort_keys=False).strip()
            full_content = f"---\n{frontmatter_str}\n---\n\n{content.strip()}\n"
        else:
            full_content = content

        skill_md.write_text(full_content, encoding="utf-8")
        return SkillsService._parse_skill_file(skill_md)

    @staticmethod
    def delete_skill(skill_id: str) -> bool:
        """
        Removes a custom skill directory from ~/.openagents/skills/.
        """
        import shutil
        skills_dir = get_skills_dir()
        target_dir = skills_dir / skill_id
        if target_dir.exists() and target_dir.is_dir():
            shutil.rmtree(target_dir)
            return True
        return False

    @staticmethod
    def get_skills_prompt_summary() -> str:
        """
        Generates a concise system prompt summary of available ~/.openagents/skills.
        """
        skills = SkillsService.list_skills()
        if not skills:
            return ""

        lines = ["## Available OpenAgents Skills (~/.openagents/skills):"]
        for s in skills:
            desc = s.get("description", "No description provided.")
            lines.append(f"- **{s['name']}** (`{s['id']}`): {desc}")
        lines.append("\nTo view full skill workflows, reference the skill's SKILL.md.")
        return "\n".join(lines)
