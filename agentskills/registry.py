"""
Skill Registry - Aggregates skills from multiple providers.

The registry provides:
- Unified access to skills from all providers
- Search with fuzzy matching
- Pagination for large skill sets
- Caching for performance
"""
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from .models import Skill
from .providers import SkillProvider, AnthropicSkillProvider


@dataclass
class SearchResult:
    """Paginated search results."""
    skills: list[Skill]
    total: int
    page: int
    per_page: int
    
    @property
    def total_pages(self) -> int:
        return (self.total + self.per_page - 1) // self.per_page
    
    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
    
    @property
    def has_prev(self) -> bool:
        return self.page > 1


class SkillRegistry:
    """
    Central registry that aggregates skills from multiple providers.
    
    Usage:
        registry = SkillRegistry()
        registry.add_provider(AnthropicSkillProvider())
        
        # Browse all
        results = registry.browse(page=1, per_page=20)
        
        # Search
        results = registry.search("mcp", page=1)
        
        # Get specific skill
        skill = registry.get("mcp-builder")
    """
    
    def __init__(self):
        self._providers: list[SkillProvider] = []
        self._skills: list[Skill] = []
        self._loaded = False
    
    def add_provider(self, provider: SkillProvider) -> None:
        """Add a skill provider."""
        self._providers.append(provider)
        self._loaded = False
    
    def refresh(self, force: bool = False) -> None:
        """Refresh skills from all providers."""
        self._skills = []
        for provider in self._providers:
            try:
                skills = provider.fetch_skills(force_refresh=force)
                self._skills.extend(skills)
            except Exception as e:
                print(f"Warning: Failed to fetch from {provider.name}: {e}")
        self._loaded = True
    
    def _ensure_loaded(self) -> None:
        """Ensure skills are loaded."""
        if not self._loaded:
            self.refresh()
    
    def browse(
        self,
        page: int = 1,
        per_page: int = 20,
        source: Optional[str] = None
    ) -> SearchResult:
        """
        Browse all skills with pagination.
        
        Args:
            page: Page number (1-indexed)
            per_page: Skills per page
            source: Filter by source (e.g., "anthropic")
        """
        self._ensure_loaded()
        
        # Filter by source if specified
        skills = self._skills
        if source:
            skills = [s for s in skills if s.source == source]
        
        # Sort by name
        skills = sorted(skills, key=lambda s: s.name.lower())
        
        # Paginate
        total = len(skills)
        start = (page - 1) * per_page
        end = start + per_page
        page_skills = skills[start:end]
        
        return SearchResult(
            skills=page_skills,
            total=total,
            page=page,
            per_page=per_page
        )
    
    def search(
        self,
        query: str,
        page: int = 1,
        per_page: int = 20,
        source: Optional[str] = None
    ) -> SearchResult:
        """
        Search skills by name, description, or tags.
        
        Args:
            query: Search query
            page: Page number (1-indexed)
            per_page: Skills per page
            source: Filter by source
        """
        self._ensure_loaded()
        
        # Filter by query and source
        matches = []
        for skill in self._skills:
            if source and skill.source != source:
                continue
            if skill.matches(query):
                matches.append(skill)
        
        # Sort by relevance (name match first, then description)
        query_lower = query.lower()
        matches.sort(key=lambda s: (
            0 if query_lower in s.name.lower() else 1,
            s.name.lower()
        ))
        
        # Paginate
        total = len(matches)
        start = (page - 1) * per_page
        end = start + per_page
        page_skills = matches[start:end]
        
        return SearchResult(
            skills=page_skills,
            total=total,
            page=page,
            per_page=per_page
        )
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by exact name."""
        self._ensure_loaded()
        
        for skill in self._skills:
            if skill.name == name:
                return skill
        return None
    
    def install(self, skill: Skill, target_dir: Optional[Path] = None) -> Path:
        """
        Install a skill to the target directory.
        
        Args:
            skill: Skill to install
            target_dir: Target directory (default: .skills/)
        
        Returns:
            Path to installed skill
        """
        if target_dir is None:
            target_dir = Path.cwd() / ".skills"
        
        # Find the provider for this skill
        for provider in self._providers:
            if provider.source_id == skill.source:
                return provider.install_skill(skill, target_dir)
        
        raise ValueError(f"No provider found for skill source: {skill.source}")
    
    @property
    def total_skills(self) -> int:
        """Total number of skills across all providers."""
        self._ensure_loaded()
        return len(self._skills)
    
    @property
    def sources(self) -> list[str]:
        """List of available sources."""
        return [p.source_id for p in self._providers]


# Convenience function to create a default registry
def create_default_registry() -> SkillRegistry:
    """Create a registry with default providers."""
    registry = SkillRegistry()
    registry.add_provider(AnthropicSkillProvider())
    return registry
