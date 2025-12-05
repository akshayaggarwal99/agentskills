# 🧠 AgentSkills

**A CLI for browsing, searching, and installing skills from [anthropics/skills](https://github.com/anthropics/skills).**

Skills are folders of instructions and resources that teach Claude how to complete specific tasks. This CLI makes it easy to discover and use them.

## Installation

```bash
pip install agentskills
```

Or install from source:

```bash
git clone https://github.com/akshayaggarwal99/agentskills.git
cd agentskills
pip install -e .
```

## Quick Start

```bash
# Browse all available skills
skill browse

# Search for specific skills
skill search mcp
skill search "frontend design"

# View skill details
skill get mcp-builder

# Install a skill to your project
skill use mcp-builder

# Create ZIP for Claude.ai upload
skill zip mcp-builder

# Remove an installed skill
skill remove mcp-builder
```

## Commands

| Command | Description |
|---------|-------------|
| `skill browse` | 📚 Browse all skills (paginated) |
| `skill search <query>` | 🔍 Search by name, description, or tags |
| `skill get <name>` | 📄 View skill details and SKILL.md preview |
| `skill use <name>` | ⬇️ Install skill to `.skills/` directory |
| `skill zip <name>` | 📦 Create ZIP for Claude.ai upload |
| `skill remove <name>` | 🗑️ Remove an installed skill |
| `skill stats` | 📊 Show registry statistics |

## Usage with Claude

### Claude Code
Skills installed to `.skills/` are automatically available. Just mention the skill:
```
"Use the mcp-builder skill to create a GitHub API server"
```

### Claude.ai
1. Install and zip the skill:
   ```bash
   skill use frontend-design
   skill zip frontend-design
   ```
2. Go to [claude.ai/settings/capabilities](https://claude.ai/settings/capabilities)
3. Upload the ZIP file

### Claude API
Reference the `SKILL.md` file directly in your prompts or use the [Skills API](https://docs.anthropic.com/en/api/skills-guide).

## How It Works

This CLI fetches skills from the official [anthropics/skills](https://github.com/anthropics/skills) repository and caches them locally at `~/.agentskills/cache/`.

Skills follow the [Agent Skills Spec](https://github.com/anthropics/skills/blob/main/spec/agent-skills-spec.md):
- Each skill is a folder with a `SKILL.md` file
- YAML frontmatter defines `name` and `description`
- Markdown body contains instructions for Claude

## Available Skills

| Skill | Description |
|-------|-------------|
| `mcp-builder` | Guide for creating MCP servers |
| `frontend-design` | Create production-grade UIs |
| `webapp-testing` | Test web apps with Playwright |
| `pdf` | PDF manipulation toolkit |
| `docx` | Word document creation |
| `pptx` | PowerPoint generation |
| `xlsx` | Excel spreadsheet creation |
| ... | [Browse all 16+ skills](https://github.com/anthropics/skills) |

## Architecture

```
agentskills/
├── models.py      # Skill dataclass
├── providers.py   # SkillProvider abstraction (Anthropic, Local)
├── registry.py    # Multi-provider registry with search/pagination
└── cli.py         # Typer CLI commands
```

**Extensible design**: Add new skill sources by implementing `SkillProvider`:

```python
from agentskills.providers import SkillProvider, LocalSkillProvider
from agentskills.registry import SkillRegistry

registry = SkillRegistry()
registry.add_provider(AnthropicSkillProvider())
registry.add_provider(LocalSkillProvider(Path("./my-skills")))
```

## License

MIT License - see [LICENSE](LICENSE) for details.

## Credits

- Skills sourced from [anthropics/skills](https://github.com/anthropics/skills) (Apache 2.0)
- Built with [Typer](https://typer.tiangolo.com/) and [Rich](https://rich.readthedocs.io/)

## Contributing

Contributions welcome! Please open an issue or PR.
