"""
Skill data models.
"""
from dataclasses import dataclass, field
from typing import Optional
from pathlib import Path


@dataclass
class Skill:
    """Represents an agent skill."""
    name: str
    description: str
    source: str  # e.g., "anthropic", "community", "local"
    
    # Content
    content: str = ""  # Full SKILL.md content
    folder_path: Optional[str] = None  # Path on disk
    
    # Metadata
    license: Optional[str] = None
    author: Optional[str] = None
    tags: list[str] = field(default_factory=list)
    version: Optional[str] = None
    
    # Computed properties
    @property
    def has_scripts(self) -> bool:
        """Check if skill has scripts folder."""
        if not self.folder_path:
            return False
        return (Path(self.folder_path) / "scripts").exists()
    
    @property
    def has_references(self) -> bool:
        """Check if skill has reference docs."""
        if not self.folder_path:
            return False
        return (Path(self.folder_path) / "reference").exists()
    
    def matches(self, query: str) -> bool:
        """Check if skill matches a search query."""
        query_lower = query.lower()
        return (
            query_lower in self.name.lower() or
            query_lower in self.description.lower() or
            any(query_lower in tag.lower() for tag in self.tags)
        )
