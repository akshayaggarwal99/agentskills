"""
AgentSkills - Universal Agent Skill Registry

A CLI for browsing, searching, and installing skills from the
official anthropics/skills repository.

Architecture:
- SkillProvider: Abstract base for skill sources (GitHub, local, etc.)
- AnthropicSkillProvider: Fetches skills from anthropics/skills
- SkillRegistry: Aggregates multiple providers
- CLI: User interface with search, browse, pagination
"""
from .registry import SkillRegistry, Skill
from .providers import AnthropicSkillProvider

__version__ = "0.2.0"
__all__ = ["SkillRegistry", "Skill", "AnthropicSkillProvider"]
