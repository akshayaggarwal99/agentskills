"""
Skill Providers - Abstract base and implementations for skill sources.

Providers are pluggable sources of skills. Each provider knows how to:
- Fetch skills from its source (GitHub, local folder, etc.)
- Parse skill metadata
- Install skills to a target directory
"""
import subprocess
import shutil
import yaml
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .models import Skill


class SkillProvider(ABC):
    """Abstract base class for skill providers."""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable provider name."""
        pass
    
    @property
    @abstractmethod
    def source_id(self) -> str:
        """Short identifier for this source (e.g., 'anthropic')."""
        pass
    
    @abstractmethod
    def fetch_skills(self, force_refresh: bool = False) -> list[Skill]:
        """Fetch all available skills from this provider."""
        pass
    
    @abstractmethod
    def install_skill(self, skill: Skill, target_dir: Path) -> Path:
        """Install a skill to the target directory. Returns installed path."""
        pass


class AnthropicSkillProvider(SkillProvider):
    """
    Provider for official Anthropic skills from github.com/anthropics/skills.
    
    Clones the repo locally and parses SKILL.md files.
    """
    
    REPO_URL = "https://github.com/anthropics/skills.git"
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / ".agentskills" / "cache" / "anthropic-skills"
        self._skills: list[Skill] = []
    
    @property
    def name(self) -> str:
        return "Anthropic Official Skills"
    
    @property
    def source_id(self) -> str:
        return "anthropic"
    
    def fetch_skills(self, force_refresh: bool = False) -> list[Skill]:
        """Fetch skills from anthropics/skills repo."""
        self._ensure_cache(force_refresh)
        self._skills = self._parse_skills()
        return self._skills
    
    def install_skill(self, skill: Skill, target_dir: Path) -> Path:
        """Copy skill folder to target directory."""
        if not skill.folder_path:
            raise ValueError(f"Skill {skill.name} has no folder path")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        skill_source = Path(skill.folder_path)
        skill_target = target_dir / skill.name
        
        if skill_target.exists():
            shutil.rmtree(skill_target)
        
        shutil.copytree(skill_source, skill_target)
        return skill_target
    
    def _ensure_cache(self, force_refresh: bool = False) -> None:
        """Clone or update the repo cache."""
        if self.cache_dir.exists() and not force_refresh:
            # Try to update
            try:
                subprocess.run(
                    ["git", "pull", "--quiet"],
                    cwd=self.cache_dir,
                    check=True,
                    capture_output=True,
                    timeout=30
                )
                return
            except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
                # Re-clone on failure
                shutil.rmtree(self.cache_dir)
        
        self._clone_repo()
    
    def _clone_repo(self) -> None:
        """Clone the anthropics/skills repository."""
        self.cache_dir.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            ["git", "clone", "--depth", "1", self.REPO_URL, str(self.cache_dir)],
            check=True,
            capture_output=True,
            timeout=60
        )
    
    def _parse_skills(self) -> list[Skill]:
        """Parse all SKILL.md files in the cache."""
        skills_dir = self.cache_dir / "skills"
        if not skills_dir.exists():
            return []
        
        skills = []
        for folder in skills_dir.iterdir():
            if not folder.is_dir():
                continue
            
            skill_md = folder / "SKILL.md"
            if not skill_md.exists():
                continue
            
            try:
                skill = self._parse_skill_md(skill_md.read_text(), str(folder))
                if skill:
                    skills.append(skill)
            except Exception:
                continue  # Skip malformed skills
        
        return skills
    
    def _parse_skill_md(self, content: str, folder_path: str) -> Optional[Skill]:
        """Parse a SKILL.md file with YAML frontmatter."""
        if not content.startswith("---"):
            return None
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None
        
        if not frontmatter or "name" not in frontmatter:
            return None
        
        # Extract tags from description keywords
        description = frontmatter.get("description", "")
        tags = self._extract_tags(description)
        
        return Skill(
            name=frontmatter["name"],
            description=description,
            source=self.source_id,
            content=content,
            folder_path=folder_path,
            license=frontmatter.get("license"),
            author="Anthropic",
            tags=tags
        )
    
    def _extract_tags(self, description: str) -> list[str]:
        """Extract category tags from description."""
        tags = []
        keywords = {
            "pdf": ["pdf", "document"],
            "docx": ["docx", "document", "word"],
            "pptx": ["pptx", "presentation", "slides"],
            "xlsx": ["xlsx", "spreadsheet", "excel"],
            "design": ["design", "frontend", "ui"],
            "mcp": ["mcp", "server", "api"],
            "art": ["art", "creative", "visual"],
            "testing": ["testing", "qa", "playwright"],
        }
        
        desc_lower = description.lower()
        for tag, kws in keywords.items():
            if any(kw in desc_lower for kw in kws):
                tags.append(tag)
        
        return tags


class LocalSkillProvider(SkillProvider):
    """
    Provider for local skills in a directory.
    
    Useful for development or custom skills.
    """
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self._skills: list[Skill] = []
    
    @property
    def name(self) -> str:
        return f"Local Skills ({self.skills_dir})"
    
    @property
    def source_id(self) -> str:
        return "local"
    
    def fetch_skills(self, force_refresh: bool = False) -> list[Skill]:
        """Scan local directory for skills."""
        if not self.skills_dir.exists():
            return []
        
        self._skills = []
        for folder in self.skills_dir.iterdir():
            if not folder.is_dir():
                continue
            
            skill_md = folder / "SKILL.md"
            if skill_md.exists():
                try:
                    content = skill_md.read_text()
                    skill = self._parse_skill_md(content, str(folder))
                    if skill:
                        self._skills.append(skill)
                except Exception:
                    continue
        
        return self._skills
    
    def install_skill(self, skill: Skill, target_dir: Path) -> Path:
        """Copy skill folder to target directory."""
        if not skill.folder_path:
            raise ValueError(f"Skill {skill.name} has no folder path")
        
        target_dir.mkdir(parents=True, exist_ok=True)
        skill_target = target_dir / skill.name
        
        if skill_target.exists():
            shutil.rmtree(skill_target)
        
        shutil.copytree(skill.folder_path, skill_target)
        return skill_target
    
    def _parse_skill_md(self, content: str, folder_path: str) -> Optional[Skill]:
        """Parse SKILL.md with YAML frontmatter."""
        if not content.startswith("---"):
            return None
        
        parts = content.split("---", 2)
        if len(parts) < 3:
            return None
        
        try:
            frontmatter = yaml.safe_load(parts[1])
        except yaml.YAMLError:
            return None
        
        if not frontmatter or "name" not in frontmatter:
            return None
        
        return Skill(
            name=frontmatter["name"],
            description=frontmatter.get("description", ""),
            source=self.source_id,
            content=content,
            folder_path=folder_path,
            license=frontmatter.get("license"),
            author=frontmatter.get("author"),
            tags=frontmatter.get("tags", [])
        )
